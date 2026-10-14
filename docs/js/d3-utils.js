/* Shared D3 drawing helpers — marks(), mk(), responsive()
 * Used by dossier-flow.js, flow2a.js, flow2b.js, flow3.js
 */
function marks(s){
  var defs=s.append("defs");
  [["ag","#aebbcd"],["agg","#3fae6d"],["ago","#e0b84a"],["ab","#5f83b8"],["ap","#9a86c8"],["aa","#e0a64a"],["gg","#8b98a6"],["gr","#58c489"]].forEach(function(m){
    defs.append("marker").attr("id",m[0]).attr("viewBox","0 -5 10 10").attr("refX",8).attr("refY",0).attr("markerWidth",7).attr("markerHeight",7).attr("orient","auto").append("path").attr("d","M0,-5L10,0L0,5").attr("fill",m[1])
  });
  defs.append("marker").attr("id","agRev").attr("viewBox","0 -5 10 10").attr("refX",2).attr("refY",0).attr("markerWidth",7).attr("markerHeight",7).attr("orient","auto").append("path").attr("d","M10,-5L0,0L10,5").attr("fill","#aebbcd")
}

function mk(s){
  return{
    box:function(x,y,w,h,f,o){o=o||{};var r=s.append("rect").attr("x",x).attr("y",y).attr("width",w).attr("height",h).attr("rx",o.rx==null?14:o.rx).attr("fill",f);if(o.stroke)r.attr("stroke",o.stroke).attr("stroke-width",o.sw||1.6);if(o.dash)r.attr("stroke-dasharray",o.dash);return r},
    T:function(x,y,t,o){o=o||{};var e=s.append("text").attr("x",x).attr("y",y).attr("fill",o.fill||"#e8eef5").attr("font-size",o.fs||11).text(t);if(o.a)e.attr("text-anchor",o.a);if(o.w)e.attr("font-weight",o.w);if(o.ls)e.attr("letter-spacing",o.ls);if(o.it)e.attr("font-style","italic");if(o.rot)e.attr("transform","rotate("+o.rot+" "+x+" "+y+")");return e},
    P:function(d,st,o){o=o||{};var p=s.append("path").attr("d",d).attr("fill","none").attr("stroke",st).attr("stroke-width",o.sw||2);if(o.dash)p.attr("stroke-dasharray",o.dash);if(o.m)p.attr("marker-end","url(#"+o.m+")");if(o.cls)p.attr("class",o.cls);return p},
    Ln:function(x1,y1,x2,y2,st,o){o=o||{};var l=s.append("line").attr("x1",x1).attr("y1",y1).attr("x2",x2).attr("y2",y2).attr("stroke",st).attr("stroke-width",o.sw||2);if(o.dash)l.attr("stroke-dasharray",o.dash);if(o.m)l.attr("marker-end","url(#"+o.m+")");if(o.ms)l.attr("marker-start","url(#"+o.ms+")");if(o.cls)l.attr("class",o.cls);return l},
    C:function(cx,cy,rr,f,o){o=o||{};var c=s.append("circle").attr("cx",cx).attr("cy",cy).attr("r",rr).attr("fill",f);if(o.stroke)c.attr("stroke",o.stroke).attr("stroke-width",o.sw||1.4);return c},
    E:function(cx,cy,rx,ry,f,o){o=o||{};var e=s.append("ellipse").attr("cx",cx).attr("cy",cy).attr("rx",rx).attr("ry",ry).attr("fill",f);if(o.stroke)e.attr("stroke",o.stroke).attr("stroke-width",o.sw||1.4);return e}
  }
}

function responsive(id,vbD,vbM,desk,mob){
  if(typeof d3==='undefined') return;
  var svg=d3.select(id);
  if(svg.empty())return;
  function draw(){
    var pn=svg.node().parentNode,W=(pn&&pn.getBoundingClientRect().width)||900,m=W<560;
    svg.selectAll("*").remove();marks(svg);var a=mk(svg);
    if(m){svg.attr("viewBox",vbM);mob(a)}else{svg.attr("viewBox",vbD);desk(a)}
  }
  draw();
  var r;window.addEventListener("resize",function(){clearTimeout(r);r=setTimeout(draw,150)})
}
