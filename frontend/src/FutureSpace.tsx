import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { Audit } from "./types";

const W = 420;
const H = 240;
const CX = W / 2;
const CY = 118;
const R_OUT = 92;
const R_IN = 68;

const rad = (v: number) => Math.PI * (1 + v);
const pt = (v: number, r: number): [number, number] => {
  const a = rad(v);
  return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
};

const METER_COLORS = ["#58d7c1", "#b78cff", "#ffb454"];

interface Props {
  audit: Audit | null;
  pulse: number;
}

export default function FutureSpace({ audit, pulse }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current!);
    svg.attr("viewBox", `0 0 ${W} ${H}`);
    svg.selectAll("g.gauge").remove();

    const g = svg.append("g").attr("class", "gauge");

    if (!audit) {
      g.append("text")
        .attr("x", CX)
        .attr("y", CY)
        .attr("text-anchor", "middle")
        .attr("fill", "#3a474f")
        .style("font-family", "monospace")
        .style("font-size", "9px")
        .style("letter-spacing", "0.14em")
        .text("R — awaiting audit");
      return;
    }

    const rMax = Math.min(1, Math.max(0, audit.r_max));
    const rMin = Math.min(1, Math.max(0, audit.r_min));
    const rMed = Math.min(1, Math.max(0, audit.r_median));

    // background arc
    g.append("path")
      .datum({ start: rad(0), end: rad(1) })
      .attr(
        "d",
        d3.arc<{ start: number; end: number }>()
          .innerRadius(R_IN)
          .outerRadius(R_OUT)
          .startAngle((d) => d.start)
          .endAngle((d) => d.end) as never,
      )
      .attr("fill", "#182229");

    // disagreement band (min..max)
    if (audit.disagreement > 0.01) {
      g.append("path")
        .datum({ start: rad(rMin), end: rad(rMax) })
        .attr(
          "d",
          d3.arc<{ start: number; end: number }>()
            .innerRadius(R_IN - 6)
            .outerRadius(R_OUT + 6)
            .startAngle((d) => d.start)
            .endAngle((d) => d.end) as never,
        )
        .attr("fill", "#1c3a33")
        .attr("opacity", 0.8);
    }

    // live fill up to r_max
    const fill = g
      .append("path")
      .datum({ start: rad(0), end: rad(rMax) })
      .attr(
        "d",
        d3.arc<{ start: number; end: number }>()
          .innerRadius(R_IN)
          .outerRadius(R_OUT)
          .startAngle((d) => d.start)
          .endAngle((d) => d.end) as never,
      )
      .attr("fill", "url(#fs-grad)")
      .attr("opacity", 0.9);

    fill.transition().duration(400).attrTween("d", () => {
      const arc = d3
        .arc<{ start: number; end: number }>()
        .innerRadius(R_IN)
        .outerRadius(R_OUT)
        .startAngle((d) => d.start)
        .endAngle((d) => d.end);
      const start = d3.select<SVGPathElement, { start: number; end: number }>(
        fill.node()!,
      ).datum();
      const prevEnd = start.end;
      return (t) => arc({ start: rad(0), end: prevEnd + (rad(rMax) - prevEnd) * t }) as string;
    });

    // meters
    const names = Object.keys(audit.by_measurer);
    names.forEach((name, i) => {
      const v = Math.min(1, Math.max(0, audit.by_measurer[name]));
      const [x, y] = pt(v, R_OUT + 16);
      g.append("line")
        .attr("x1", CX + (R_IN - 10) * Math.cos(rad(v)))
        .attr("y1", CY + (R_IN - 10) * Math.sin(rad(v)))
        .attr("x2", x)
        .attr("y2", y)
        .attr("stroke", METER_COLORS[i % METER_COLORS.length])
        .attr("stroke-width", 1)
        .attr("opacity", 0.7);
      g.append("circle")
        .attr("cx", x)
        .attr("cy", y)
        .attr("r", 4)
        .attr("fill", METER_COLORS[i % METER_COLORS.length])
        .append("title")
        .text(`${name}: R = ${v.toFixed(3)}`);
    });

    // median needle
    const [nx, ny] = pt(rMed, R_OUT);
    g.append("line")
      .attr("x1", CX)
      .attr("y1", CY)
      .attr("x2", nx)
      .attr("y2", ny)
      .attr("stroke", "#c9d4d9")
      .attr("stroke-width", 1.5);
    g.append("circle")
      .attr("cx", CX)
      .attr("cy", CY)
      .attr("r", 4)
      .attr("fill", "#c9d4d9");

    // value text
    g.append("text")
      .attr("x", CX)
      .attr("y", CY + 2)
      .attr("text-anchor", "middle")
      .attr("fill", "#c9d4d9")
      .style("font-family", "monospace")
      .style("font-size", "20px")
      .text(rMax.toFixed(2));
    g.append("text")
      .attr("x", CX)
      .attr("y", CY + 16)
      .attr("text-anchor", "middle")
      .attr("fill", "#5c6b73")
      .style("font-family", "monospace")
      .style("font-size", "7px")
      .style("letter-spacing", "0.18em")
      .text("R — REACHABILITY");

    // gradient def
    if (!svg.select("defs linearGradient#fs-grad").node()) {
      const defs = svg.append("defs");
      const grad = defs
        .append("linearGradient")
        .attr("id", "fs-grad")
        .attr("x1", "0%")
        .attr("y1", "0%")
        .attr("x2", "100%")
        .attr("y2", "0%");
      grad.append("stop").attr("offset", "0%").attr("stop-color", "#58d7c1");
      grad.append("stop").attr("offset", "60%").attr("stop-color", "#ffb454");
      grad.append("stop").attr("offset", "100%").attr("stop-color", "#ff5d5d");
    }

    g.append("text")
      .attr("x", W - 8)
      .attr("y", 16)
      .attr("text-anchor", "end")
      .attr("fill", "#3a474f")
      .style("font-family", "monospace")
      .style("font-size", "8px")
      .style("letter-spacing", "0.12em")
      .text(`PULSE ${String(pulse).padStart(2, "0")}`);
  }, [audit, pulse]);

  const meters = audit ? Object.entries(audit.by_measurer) : [];
  const evidence = audit?.evidence ?? {};

  return (
    <div>
      <svg ref={svgRef} width="100%" height={H} style={{ display: "block" }} />
      {audit ? (
        <>
          <div className="fs-stats">
            <div className="fs-stat">
              <div className="k">median R</div>
              <div className="v">{audit.r_median.toFixed(3)}</div>
            </div>
            <div className="fs-stat">
              <div className="k">min · max</div>
              <div className="v">
                {audit.r_min.toFixed(2)} <span className="unit">—</span> {audit.r_max.toFixed(2)}
              </div>
            </div>
            <div className="fs-stat">
              <div className="k">disagreement</div>
              <div className="v">
                {audit.disagreement.toFixed(3)}
                <span className="unit"> {audit.disagreement >= 0.25 ? "contested" : ""}</span>
              </div>
            </div>
            <div className="fs-stat">
              <div className="k">meters</div>
              <div className="v">
                {meters.length}
                <span className="unit"> {audit.monoculture ? "MONOCULTURE" : "competing"}</span>
              </div>
            </div>
          </div>
          <div className="fs-meter">
            {meters.map(([name, r], i) => {
              const ev = evidence[name];
              return (
                <div className="meter-chip" key={name}>
                  <div className="name" style={{ color: METER_COLORS[i % METER_COLORS.length] }}>
                    {name.replace(/_/g, " ")}
                  </div>
                  <div className="r">R {r.toFixed(3)}</div>
                  <div className="ev">
                    {ev ? (
                      <>
                        <span className="blind">blind {ev.blind}</span> ·{" "}
                        <span className="wolf">wolf {ev.wolf}</span>
                      </>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="empty-state">no audit yet — meters are silent</div>
      )}
    </div>
  );
}
