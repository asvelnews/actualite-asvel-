/* sw.js — Service worker Actu ASVEL
   Alertes navigateur à l'heure du match, uniquement pendant que le navigateur
   garde ce service worker en vie (au moins un onglet du site ouvert).
   Aucun service externe : tout est calculé depuis data.js (même domaine).
   Contrôle de version : incrémenter SW_VERSION à chaque déploiement. */
'use strict';

var SW_VERSION = 2;

try { importScripts('data.js'); } catch (e) {}

function dateOfGame(g){ if(!g||!g[0])return null; var d=new Date(g[0]+'T12:00:00'); if(isNaN(d.getTime()))return null; return d; }
function kickOfGame(g){
  var base=dateOfGame(g); if(!base)return null;
  var hh=0,mm=0, t=/^(\d{1,2})h(\d{2})$/.exec(String(g[1]));
  if(t){ hh=+t[1]; mm=+t[2]; }
  var k=new Date(base); k.setHours(hh,mm,0,0); return k;
}
function compLabel(c){ if(c==='euroleague')return 'EuroLeague'; if(c==='belite')return 'Betclic ÉLITE'; if(c==='derby')return 'Derby · Betclic ÉLITE'; return ''; }

var scheduled = {};

function scheduleAll(){
  var games = (typeof self.ASVEL_GAMES === 'undefined') ? [] : self.ASVEL_GAMES;
  var now = Date.now(), pending = [];
  games.forEach(function(g){
    var k = kickOfGame(g);
    if(!k) return;
    if(k.getTime() <= now) return;           // déjà passé
    if(k.getTime() - now > 48*60*60*1000) return; // fenêtre 48 h : veille + heure du match
    pending.push({ kick: k.getTime(), g: g });
  });
  pending.sort(function(a,b){ return a.kick - b.kick; });
  var DAY = 24*60*60*1000;
  pending.forEach(function(p){
    var key = p.g[0]+'|'+p.g[2]+'|'+p.g[3];
    /* Rappel veille : 24 h avant le coup d'envoi (si encore à venir). */
    var seeWait = (p.kick - DAY) - now;
    if (seeWait > 0 && !scheduled[key+':see']) {
      scheduled[key+':see'] = setTimeout(function(){
        var title = 'Match demain !';
        var body = 'Demain : LDLC ASVEL – ' + p.g[2] + ' · ' + compLabel(p.g[4]);
        if (self.registration && self.registration.showNotification) {
          self.registration.showNotification(title, {
            body: body,
            tag: 'asvel-see-' + key,
            icon: 'favicon.svg',
            badge: 'favicon.svg'
          });
        }
        delete scheduled[key+':see'];
      }, seeWait);
    }
    if (scheduled[key+':kick']) return;      // déjà planifié dans cette vie du SW
    var wait = p.kick - now;
    scheduled[key+':kick'] = setTimeout(function(){
      var title = 'C\'est l\'heure du match !';
      var body = 'LDLC ASVEL – ' + p.g[2] + ' · ' + compLabel(p.g[4]);
      if (self.registration && self.registration.showNotification) {
        self.registration.showNotification(title, {
          body: body,
          tag: 'asvel-kick-' + key,
          icon: 'favicon.svg',
          badge: 'favicon.svg'
        });
      }
      delete scheduled[key+':kick'];
    }, wait);
  });
}

self.addEventListener('install', function(e){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(self.clients.claim()); scheduleAll(); });
self.addEventListener('message', function(){ scheduleAll(); });
self.addEventListener('notificationclick', function(e){
  e.notification.close();
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(list){
      var url = 'matchs.html';
      for (var i=0;i<list.length;i++){
        if (list[i].url.indexOf('matchs.html') !== -1) { return list[i].focus(); }
      }
      return self.clients.openWindow(url);
    })
  );
});