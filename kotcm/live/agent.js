'use strict';
// Agent de kotcm, phase 2 (spec, section 9) : lit et remplace un emplacement de l'editeur
// dans DungeonStorage, pose ou retire le patch d'« Enregistrer ». libthieves.so x86_64,
// adresses de la table du noyau (prelude ADR) : la version est gardee cote Python (appareil.py), la forme
// de la memoire est verifiee ici avant toute ecriture.
//
// Le modele n'est lu et ecrit que dans le fil du jeu, au debut d'une image (nativeDrawFrame) :
// le jeu n'y touche pas au meme moment.

var mod = Process.getModuleByName('libthieves.so');
var base = mod.base;

var VT_DS = base.add(ADR.vt_dungeon_storage);         // DungeonStorage
var VT_DONJON = base.add(ADR.vt_dungeon);             // KTProtocol::Dungeon
var VT_OBSTACLE = base.add(ADR.vt_dungeon_obstacle);  // KTProtocol::Dungeon_Obstacle
var DS = base.add(ADR.dungeon_storage);               // l'objet DungeonStorage (statique)
var UP = base.add(ADR.user_profile_ptr);              // pointeur vers UserProfile
var EDITEUR_IMAGE = base.add(ADR.editeur_image);      // SelfEditorState[8] : une fois par image dans l'editeur
var EVENEMENTS = base.add(ADR.editeur_evenement);     // SelfEditorState[2](this, evenement)
var IMAGE = mod.getExportByName('Java_com_zf_ZRenderer_nativeDrawFrame');
var serialiser = new NativeFunction(base.add(ADR.serialize_to_string), 'bool', ['pointer', 'pointer']);  // SerializeToString
var parser = new NativeFunction(base.add(ADR.parse_from_array), 'bool', ['pointer', 'pointer', 'int']);  // ParseFromArray

// « Enregistrer » (evenement 100) : call 0x1582350 (controle) ; test al, al ; je 0x1570f37 (fin).
// Le patch change ce `je` en `jmp` : le controle s'affiche encore, l'editeur ne passe jamais en
// mode enregistrer. « Essayer » (evenement 142, son propre `je` en 0x1570cf0) n'est pas touche.
var PATCH = base.add(ADR.kotcm_patch_enregistrer);    // SelfEditorState[2] + 0x8f (table du noyau)
var ORIGINE = [0x0f, 0x84, 0xd2, 0x02, 0x00, 0x00];   // je  0x1570f37
var PATCHE = [0xe9, 0xd3, 0x02, 0x00, 0x00, 0x90];    // jmp 0x1570f37 ; nop

var EMPLACEMENTS = 4, TAILLE_EMPLACEMENT = 0x48, MAX_OBJETS = 500, IMAGES = 10, DELAI_MS = 3000;

function egaux(p, attendus) {
  var u = new Uint8Array(p.readByteArray(attendus.length));
  for (var i = 0; i < attendus.length; i++) if (u[i] !== attendus[i]) return false;
  return true;
}

function etatPatch() {
  if (egaux(PATCH, ORIGINE)) return 'origine';
  if (egaux(PATCH, PATCHE)) return 'pose';
  return 'inconnu';
}

function hex(buf) {
  var u = new Uint8Array(buf), s = '';
  for (var i = 0; i < u.length; i++) s += ('0' + u[i].toString(16)).slice(-2);
  return s;
}

function depuisHex(h) {
  var u = new Uint8Array(h.length / 2);
  for (var i = 0; i < u.length; i++) u[i] = parseInt(h.substr(2 * i, 2), 16);
  return u.buffer;
}

// std::string de libc++ : court si le bit 0 du premier octet est nul (longueur = octet >> 1).
function lireString(s) {
  var b0 = s.readU8();
  if ((b0 & 1) === 0) return s.add(1).readByteArray(b0 >> 1);
  return s.add(16).readPointer().readByteArray(s.add(8).readU64().toNumber());
}

function courant() {
  var up = UP.readPointer();
  if (up.isNull()) return null;
  var q = up.add(0x18).readPointer();
  return q.isNull() ? null : q.add(0x90).readS32();
}

function emplacement(i) {
  return DS.add(0x40).readPointer().add(i * TAILLE_EMPLACEMENT);
}

// null si l'emplacement i a la forme attendue, sinon ce qui ne va pas.
function defaut(i) {
  if (!DS.readPointer().equals(VT_DS)) return 'vtable de DungeonStorage';
  if (i === null || i < 0 || i >= EMPLACEMENTS) return 'emplacement ' + i;
  var s = emplacement(i);
  if (!s.readPointer().equals(VT_DONJON)) return 'emplacement ' + i + ' : pas un Dungeon';
  var n = s.add(0x20).readS32(), rep = s.add(0x28).readPointer();
  if (n < 0 || n > MAX_OBJETS || (n > 0 && rep.isNull())) return 'emplacement ' + i + ' : ' + n + ' objets';
  for (var k = 0; k < n; k++) {
    if (!rep.add(8 * (k + 1)).readPointer().readPointer().equals(VT_OBSTACLE))
      return 'emplacement ' + i + ', objet ' + k + ' : pas un Dungeon_Obstacle';
  }
  return null;
}

// L'emplacement i serialise par le jeu. Le tampon d'une longue chaine, alloue par le jeu, n'est
// pas rendu : quelques centaines d'octets par appel.
function serialiserEnHex(i) {
  var s = Memory.alloc(24);
  s.writeU64(0); s.add(8).writeU64(0); s.add(16).writeU64(0);
  return serialiser(emplacement(i), s) ? hex(lireString(s)) : null;
}

// Execute fn(editeur, memeFil) dans le fil du jeu, au debut de la IMAGES-ieme image. editeur :
// nombre d'images de l'editeur vues entre-temps (0 = editeur ferme) ; memeFil : l'editeur tourne
// dans le fil de nativeDrawFrame (null si l'editeur est ferme). Echoue si le jeu ne dessine pas.
function dansLeJeu(fn) {
  return new Promise(function (resoudre, rejeter) {
    var vues = 0, editeur = 0, filImage = null, memeFil = null, fini = false;
    var ecouteEditeur = Interceptor.attach(EDITEUR_IMAGE, {
      onEnter: function () {
        editeur++;
        if (filImage !== null) memeFil = (memeFil !== false) && Process.getCurrentThreadId() === filImage;
      }
    });
    var ecouteImage = Interceptor.attach(IMAGE, {
      onEnter: function () {
        filImage = Process.getCurrentThreadId();
        if (fini || ++vues < IMAGES) return;
        fini = true;
        try { resoudre(fn(editeur, memeFil)); } catch (e) { rejeter(e); }
        setTimeout(fermer, 0);
      }
    });
    function fermer() { ecouteImage.detach(); ecouteEditeur.detach(); }
    setTimeout(function () {
      if (fini) return;
      fini = true;
      fermer();
      rejeter(new Error('live_jeu_ne_dessine_pas'));
    }, DELAI_MS);
  });
}

rpc.exports = {
  // Lecture seule : forme de la memoire, emplacement courant serialise, patch, editeur.
  etat: function () {
    return dansLeJeu(function (editeur, memeFil) {
      var ds = DS.readPointer().equals(VT_DS);
      var i = ds ? courant() : null;
      var d = defaut(i);
      return {ds: ds, courant: i, ok: d === null, detail: d, octets: d === null ? serialiserEnHex(i) : null,
              patch: etatPatch(), editeur: editeur > 0, meme_fil: memeFil};
    });
  },

  // Fait parser h (un Dungeon en hexadecimal) par le jeu dans l'emplacement i, puis le relit.
  // N'ecrit rien si l'editeur tourne ou si l'emplacement n'a pas la forme attendue.
  ecrire: function (i, h) {
    var octets = depuisHex(h);
    var tampon = Memory.alloc(Math.max(octets.byteLength, 1));
    tampon.writeByteArray(octets);
    return dansLeJeu(function (editeur) {
      if (editeur > 0) return {ecrit: false, detail: 'editeur'};
      var d = defaut(i);
      if (d !== null) return {ecrit: false, detail: d};
      var ok = !!parser(emplacement(i), tampon, octets.byteLength);
      var apres = defaut(i);
      return {ecrit: true, ok: ok && apres === null, detail: apres,
              octets: apres === null ? serialiserEnHex(i) : null};
    });
  },

  // Pose (true) ou retire (false) le patch d'« Enregistrer » ; rend l'etat final. Le patch reste
  // apres la fin de la session : seuls ce retrait ou un redemarrage du jeu l'enlevent.
  patcher: function (poser) {
    var actuel = etatPatch();
    if (actuel === 'inconnu') return actuel;
    if (actuel !== (poser ? 'pose' : 'origine'))
      Memory.patchCode(PATCH, ORIGINE.length, function (code) { code.writeByteArray(poser ? PATCHE : ORIGINE); });
    return etatPatch();
  },

  // Lecture seule, pour l'essai : les evenements de l'editeur pendant ms millisecondes.
  evenements: function (ms) {
    var vus = [];
    var ecoute = Interceptor.attach(EVENEMENTS, {onEnter: function (args) { vus.push(args[1].toInt32()); }});
    return new Promise(function (resoudre) {
      setTimeout(function () { ecoute.detach(); resoudre(vus); }, ms);
    });
  }
};
