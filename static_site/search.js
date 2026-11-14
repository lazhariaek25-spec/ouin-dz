/* محرك البحث داخل المتصفح — يطابق backend/search.py (المفاهيم تأتي من data/concepts.json) */
var Ouin=(function(){
var C=null,IDX=null,STOP=[],CACHE={};
function norm(s){
  s=String(s==null?"":s).toLowerCase().normalize("NFKD").replace(/\p{M}/gu,"");
  s=s.replace(/ة/g,"ه").replace(/ى/g,"ي").replace(/ـ/g,"").replace(/ؤ/g,"و").replace(/ئ/g,"ي");
  return s.replace(/['’\-_\/,.()]/g," ").split(/\s+/).filter(Boolean).join(" ");
}
function jget(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.json()})}
function init(){
  if(!C)C=Promise.all([jget("data/concepts.json"),jget("data/index.json")]).then(function(a){
    STOP=a[0].stop;IDX=a[1];
    return a[0].c.map(function(c){return{sec:c[0],subs:c[1],terms:c[2]}});
  });
  return C;
}
function wil(c){
  if(!CACHE[c])CACHE[c]=jget("data/"+c+".json").then(function(rows){
    return rows.map(function(r){
      var o={osm_id:r[0],wilaya:r[1],sector:r[2],subtype:r[3],name:r[4],name_ar:r[5],name_fr:r[6],
        phone:r[7],opening_hours:r[8],website:r[9],address:r[10],lat:r[11],lon:r[12],source:null};
      o.ntext=norm([r[4],r[5],r[6],r[3],r[10]].join(" "));
      return o;
    });
  }).catch(function(){return[]});
  return CACHE[c];
}
function hit(t,qn,toks){return(t.length>=4&&qn.indexOf(t)>-1)||toks.indexOf(t)>-1}
function parse(q,cons){
  var qn=norm(q),toks=qn?qn.split(" "):[];
  var cs=cons.filter(function(c){return c.terms.some(function(t){return hit(t,qn,toks)})});
  var used=[];
  cs.forEach(function(c){c.terms.forEach(function(t){if(hit(t,qn,toks))used.push(t)})});
  var rest=toks.filter(function(w){
    return STOP.indexOf(w)<0&&!used.some(function(t){return w===t||(t.length>=4&&w.indexOf(t)>-1)});
  });
  return{qn:qn,cs:cs,rest:rest};
}
function score(r,cs){
  var tot=0;
  cs.forEach(function(c){
    if(c.subs===null){if(r.sector===c.sec)tot+=2}
    else if(c.subs.indexOf(r.subtype)>-1)tot+=10;
    else if(r.sector===c.sec&&c.terms.some(function(t){return t.length>=4&&r.ntext.indexOf(t)>-1}))tot+=6;
  });
  return tot;
}
function hav(a,b,c,d){var p=Math.PI/180,x=Math.sin((c-a)*p/2),y=Math.sin((d-b)*p/2);
  return 12742*Math.asin(Math.sqrt(x*x+Math.cos(a*p)*Math.cos(c*p)*y*y))}
function search(p){
  return init().then(function(cons){
    var codes=p.wilaya?[String(p.wilaya).padStart(2,"0")]:Object.keys(IDX);
    return Promise.all(codes.map(wil)).then(function(parts){
      var rows=[].concat.apply([],parts),related=false,out;
      if(p.sector)rows=rows.filter(function(r){return r.sector===p.sector});
      var q=String(p.q||"").trim().slice(0,80),ps=q?parse(q,cons):{qn:"",cs:[],rest:[]};
      if(ps.cs.length){
        var secs={};ps.cs.forEach(function(c){secs[c.sec]=1});
        rows=rows.filter(function(r){return secs[r.sector]});
        var specific=ps.cs.filter(function(c){return c.subs!==null}).length,need=specific?6:2;
        rows.forEach(function(r){r._s=score(r,ps.cs)});
        var hits=rows.filter(function(r){return r._s>=need});
        if(!hits.length&&rows.length){
          hits=rows.filter(function(r){return r._s>=2});
          if(!hits.length)hits=rows;
          related=true;
        }
        if(specific>=2&&hits.length&&!related){
          var top=Math.max.apply(null,hits.map(function(r){return r._s}));
          hits=hits.filter(function(r){return r._s>=top});
        }
        out=hits;
        out.forEach(function(r){r._s+=3*ps.rest.filter(function(w){return r.ntext.indexOf(w)>-1}).length});
      }else if(q){
        var toks=ps.qn.split(" ").filter(Boolean);
        out=rows.filter(function(r){return toks.every(function(w){return r.ntext.indexOf(w)>-1})});
        if(!out.length&&toks.length>1)out=rows.filter(function(r){return toks.some(function(w){return r.ntext.indexOf(w)>-1})});
        out.forEach(function(r){r._s=toks.filter(function(w){return r.ntext.indexOf(w)>-1}).length});
      }else{out=rows;out.forEach(function(r){r._s=0})}
      var geo=p.lat!=null&&p.lon!=null;
      out=out.map(function(r){
        var o=Object.assign({},r);
        if(geo)o.km=Math.round(hav(+p.lat,+p.lon,r.lat,r.lon)*100)/100;
        if(related)o.related=true;
        return o;
      });
      out.sort(function(a,b){return(b._s-a._s)||((a.km||0)-(b.km||0))});
      return out.slice(0,Math.min(+p.limit||50,200)).map(function(o){delete o.ntext;delete o._s;return o});
    });
  });
}
return{search:search,index:function(){return init().then(function(){return IDX})}};
})();
