import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { PulseMessage } from "./types";

interface SeriesSpec {
  key: string;
  color: string;
  label: string;
}

interface ChartSpec {
  title: string;
  series: SeriesSpec[];
  domain: [number, number] | "auto";
}

const CHARTS: ChartSpec[] = [
  {
    title: "economy",
    series: [
      { key: "production", color: "#8fa2ab", label: "production" },
      { key: "F", color: "#ffb454", label: "F delivered" },
    ],
    domain: "auto",
  },
  {
    title: "pathology",
    series: [
      { key: "ADI", color: "#ff5d5d", label: "ADI" },
      { key: "capture", color: "#b78cff", label: "capture" },
      { key: "avg_inversion", color: "#ff9b6a", label: "inversion" },
    ],
    domain: "auto",
  },
  {
    title: "recovery",
    series: [
      { key: "recoverability", color: "#7ee08a", label: "R proxy" },
      { key: "CR", color: "#58d7c1", label: "CR" },
      { key: "openness", color: "#ffb454", label: "openness" },
      { key: "trust", color: "#8fa2ab", label: "trust/100" },
    ],
    domain: [0, 1],
  },
];

const W = 360;
const H = 130;
const M = { top: 10, right: 10, bottom: 20, left: 30 };

function MiniChart({
  spec,
  pulses,
}: {
  spec: ChartSpec;
  pulses: PulseMessage[];
}) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const svg = d3.select(ref.current!);
    svg.selectAll("*").remove();
    const innerW = W - M.left - M.right;
    const innerH = H - M.top - M.bottom;

    const data = pulses;
    if (data.length < 2) {
      svg
        .append("text")
        .attr("x", W / 2)
        .attr("y", H / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#3a474f")
        .style("font-family", "monospace")
        .style("font-size", "8px")
        .style("letter-spacing", "0.1em")
        .text("awaiting pulse stream");
      return;
    }

    const x = d3
      .scaleLinear()
      .domain(d3.extent(data, (d) => d.metrics.pulse) as [number, number])
      .range([0, innerW]);

    let yDomain: [number, number];
    if (spec.domain === "auto") {
      const all = data.flatMap((d) =>
        spec.series.map((s) => d.metrics[s.key as keyof typeof d.metrics] as number),
      );
      const max = Math.max(1, ...all);
      yDomain = [0, max * 1.1];
    } else {
      yDomain = spec.domain;
    }
    const y = d3.scaleLinear().domain(yDomain).range([innerH, 0]).nice();

    const g = svg
      .append("g")
      .attr("transform", `translate(${M.left},${M.top})`);

    g.append("g")
      .attr("class", "grid")
      .selectAll("line")
      .data(y.ticks(4))
      .enter()
      .append("line")
      .attr("x1", 0)
      .attr("x2", innerW)
      .attr("y1", (d) => y(d))
      .attr("y2", (d) => y(d))
      .attr("stroke", "#182229")
      .attr("stroke-dasharray", "2 4");

    g.append("g")
      .selectAll("text")
      .data(y.ticks(4))
      .enter()
      .append("text")
      .attr("x", -4)
      .attr("y", (d) => y(d) + 3)
      .attr("text-anchor", "end")
      .attr("fill", "#3a474f")
      .style("font-family", "monospace")
      .style("font-size", "7px")
      .text((d) => String(d));

    g.append("g")
      .selectAll("text")
      .data(x.ticks(8))
      .enter()
      .append("text")
      .attr("x", (d) => x(d))
      .attr("y", innerH + 14)
      .attr("text-anchor", "middle")
      .attr("fill", "#3a474f")
      .style("font-family", "monospace")
      .style("font-size", "7px")
      .text((d) => String(d));

    spec.series.forEach((s, idx) => {
      const line = d3
        .line<PulseMessage>()
        .x((d) => x(d.metrics.pulse))
        .y((d) => y(d.metrics[s.key as keyof typeof d.metrics] as number))
        .curve(d3.curveMonotoneX);
      g.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", s.color)
        .attr("stroke-width", idx === 0 ? 1.8 : 1.2)
        .attr("opacity", idx === 0 ? 1 : 0.85)
        .attr("d", line as never);
    });

    const last = data[data.length - 1];
    spec.series.forEach((s) => {
      const v = last.metrics[s.key as keyof typeof last.metrics] as number;
      g.append("circle")
        .attr("cx", x(last.metrics.pulse))
        .attr("cy", y(v))
        .attr("r", 2.2)
        .attr("fill", s.color);
    });
  }, [spec, pulses]);

  return (
    <div className="tl-chart">
      <div className="head">{spec.title}</div>
      <svg ref={ref} viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ display: "block" }} />
      <div className="tl-legend">
        {spec.series.map((s) => (
          <span key={s.key}>
            <span style={{ color: s.color, content: "" }}>{s.label}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

export default function PulseTimeline({ pulses }: { pulses: PulseMessage[] }) {
  return (
    <div className="tl-row">
      {CHARTS.map((c) => (
        <MiniChart key={c.title} spec={c} pulses={pulses} />
      ))}
    </div>
  );
}
