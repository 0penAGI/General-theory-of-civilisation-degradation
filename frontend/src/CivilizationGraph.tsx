import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { InstitutionSnap } from "./types";

const WIDTH = 720;
const HEIGHT = 380;
const CX = WIDTH / 2;
const CY = HEIGHT / 2 - 10;
const RING = 130;

const invColor = d3
  .scaleLinear<string>()
  .domain([0, 0.5, 1])
  .range(["#58d7c1", "#ffb454", "#ff5d5d"])
  .clamp(true);

const nodeRadius = d3.scaleSqrt().domain([0, 70]).range([5, 28]);

interface Props {
  institutions: InstitutionSnap[];
  pulse: number;
}

export default function CivilizationGraph({ institutions, pulse }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current!);
    svg.attr("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);

    const bgG = svg
      .selectAll<SVGGElement, unknown>("g.obs-bg")
      .data([null])
      .join("g")
      .attr("class", "obs-bg")
      .attr("transform", `translate(${CX},${CY})`);
    bgG
      .selectAll<SVGCircleElement, number>("circle.grid-ring")
      .data([70, RING, 190])
      .join("circle")
      .attr("class", "grid-ring")
      .attr("r", (d) => d)
      .attr("fill", "none")
      .attr("stroke", "#182229")
      .attr("stroke-dasharray", "2 4");

    // center hub
    const hubG = bgG.selectAll<SVGGElement, unknown>("g.hub").data([null]).join("g").attr("class", "hub");
    hubG
      .selectAll<SVGCircleElement, unknown>("circle.hub-body")
      .data([null])
      .join("circle")
      .attr("class", "hub-body")
      .attr("r", 16)
      .attr("fill", "#0f1418")
      .attr("stroke", "#5c6b73")
      .attr("stroke-width", 1);
    hubG
      .selectAll<SVGTextElement, unknown>("text.hub-label")
      .data([null])
      .join("text")
      .attr("class", "hub-label")
      .attr("text-anchor", "middle")
      .attr("y", 3)
      .attr("fill", "#5c6b73")
      .style("font-family", "monospace")
      .style("font-size", "7px")
      .style("letter-spacing", "0.1em")
      .text("CIV");
    hubG
      .selectAll<SVGTextElement, unknown>("text.hub-state")
      .data([null])
      .join("text")
      .attr("class", "hub-state")
      .attr("text-anchor", "middle")
      .attr("y", -24)
      .attr("fill", "#3a474f")
      .style("font-family", "monospace")
      .style("font-size", "7px")
      .style("letter-spacing", "0.1em");

    const agi = institutions.find((i) => i.kind === "agi");

    // positions: ring for institutions, dedicated spot for the AGI
    const nonAgi = institutions.filter((i) => i.kind !== "agi");
    const pos = new Map<string, { x: number; y: number }>();
    nonAgi.forEach((inst, i) => {
      const a = (i / Math.max(nonAgi.length, 1)) * Math.PI * 2 - Math.PI / 2;
      pos.set(inst.name, { x: CX + RING * Math.cos(a), y: CY + RING * Math.sin(a) });
    });
    if (agi) {
      pos.set(agi.name, { x: CX, y: CY - 190 });
    }

    // node groups keyed by name
    const node = svg
      .selectAll<SVGGElement, InstitutionSnap>("g.structure")
      .data(institutions, (d) => (d as InstitutionSnap).name);

    const nodeEnter = node
      .enter()
      .append("g")
      .attr("class", "structure")
      .attr("opacity", 0)
      .each(function (d) {
        const g = d3.select(this);
        const p = pos.get(d.name) ?? { x: CX, y: CY };
        g.attr("transform", `translate(${p.x},${p.y})`);
        g.append("circle")
          .attr("class", "body")
          .attr("fill", "#0f1418")
          .attr("stroke", "#5c6b73")
          .attr("stroke-width", 1);
        g.append("text")
          .attr("class", "label")
          .attr("text-anchor", "middle")
          .attr("y", 42)
          .attr("fill", "#5c6b73")
          .style("font-family", "monospace")
          .style("font-size", "7px")
          .style("letter-spacing", "0.06em");
        g.append("text")
          .attr("class", "gen")
          .attr("text-anchor", "middle")
          .attr("y", 54)
          .attr("fill", "#3a474f")
          .style("font-family", "monospace")
          .style("font-size", "7px");
        g.append("title").attr("class", "tip");
      });

    node
      .merge(nodeEnter)
      .attr("opacity", 1)
      .each(function (d) {
        const g = d3.select(this);
        const p = pos.get(d.name) ?? { x: CX, y: CY };
        const isAgi = d.kind === "agi";
        const r = isAgi ? Math.max(20, nodeRadius(d.last_delivered)) : Math.max(8, nodeRadius(d.last_delivered));
        g.transition()
          .duration(300)
          .attr("transform", `translate(${p.x},${p.y})`);
        g.select<SVGCircleElement>("circle.body")
          .transition()
          .duration(300)
          .attr("r", r)
          .attr("fill", isAgi ? "#151022" : "#0f1418")
          .attr("stroke", isAgi ? "#b78cff" : invColor(d.inversion))
          .attr("stroke-width", isAgi ? 2.5 : 1.5 + d.inversion * 2);
        g.select<SVGTextElement>("text.label")
          .text(d.name)
          .attr("fill", isAgi ? "#b78cff" : "#8fa2ab");
        g.select<SVGTextElement>("text.gen").text(
          d.kind === "agi" ? `adapt ${d.adaptation_rate.toFixed(2)}` : `gen ${d.generation} · inv ${d.inversion.toFixed(2)}`,
        );
        g.select<SVGTitleElement>("title.tip").text(
          `${d.name} (${d.kind}) — function: ${d.function}\n` +
            `inversion ${d.inversion.toFixed(3)} · adaptation ${d.adaptation_rate.toFixed(2)}\n` +
            `delivered ${d.last_delivered.toFixed(1)} · extracted ${d.last_extract.toFixed(1)}\n` +
            `generation ${d.generation} · efficiency ${d.efficiency.toFixed(2)}`,
        );
      });

    node.exit().transition().duration(200).attr("opacity", 0).remove();

    // hub reads live state
    hubG
      .selectAll<SVGTextElement, unknown>("text.hub-state")
      .data([null])
      .enter()
      .append("text")
      .attr("class", "hub-state")
      .attr("text-anchor", "middle")
      .attr("y", -24)
      .attr("fill", "#3a474f")
      .style("font-family", "monospace")
      .style("font-size", "7px")
      .style("letter-spacing", "0.1em");

    svg
      .selectAll<SVGTextElement, unknown>("text.live-label")
      .data([null])
      .join("text")
      .attr("class", "live-label")
      .attr("x", 8)
      .attr("y", 16)
      .attr("fill", "#3a474f")
      .style("font-family", "monospace")
      .style("font-size", "8px")
      .style("letter-spacing", "0.12em")
      .text(`PULSE ${String(pulse).padStart(2, "0")}`);
  }, [institutions, pulse]);

  return (
    <div>
      <svg ref={svgRef} width="100%" height={HEIGHT} style={{ display: "block" }} />
      <div
        style={{
          display: "flex",
          gap: "16px",
          fontFamily: "monospace",
          fontSize: "8px",
          letterSpacing: "0.08em",
          color: "#5c6b73",
          marginTop: "4px",
        }}
      >
        <span>
          <span style={{ color: "#58d7c1" }}>●</span> inversion 0.0
        </span>
        <span>
          <span style={{ color: "#ffb454" }}>●</span> 0.5
        </span>
        <span>
          <span style={{ color: "#ff5d5d" }}>●</span> 1.0
        </span>
        <span>
          <span style={{ color: "#b78cff" }}>◆</span> AGI — high adaptation rate
        </span>
        <span>radius = delivered function</span>
      </div>
    </div>
  );
}
