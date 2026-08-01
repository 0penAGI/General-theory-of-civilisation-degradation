import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { NetworkPayload } from "./types";

interface Props {
  network: NetworkPayload;
  selectedId: string | null;
  myId: string | null;
  onSelect: (id: string) => void;
}

interface GNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  sealed: boolean;
  source: "seed" | "local";
}

interface GLink extends d3.SimulationLinkDatum<GNode> {
  kind: "fork" | "adopt" | "seal";
}

const WIDTH = 920;
const HEIGHT = 520;

export default function LineageGraph({ network, selectedId, myId, onSelect }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    const nodes: GNode[] = network.nodes.map((n) => ({
      id: n.id,
      name: n.name,
      sealed: n.sealed,
      source: n.source,
    }));
    const nodeById = new Map(nodes.map((n) => [n.id, n]));

    const links: GLink[] = [];
    for (const n of network.nodes) {
      if (n.parent_node !== "-" && nodeById.has(n.parent_node)) {
        links.push({ source: n.parent_node, target: n.id, kind: "fork" });
      }
      for (const d of n.adopted) {
        const from = d.adopted_node;
        if (from && from !== n.id && nodeById.has(from)) {
          links.push({ source: from, target: n.id, kind: "adopt" });
        }
      }
      if (n.sealed && n.superseded_by && nodeById.has(n.superseded_by)) {
        links.push({ source: n.id, target: n.superseded_by, kind: "seal" });
      }
    }

    const root = d3.select(svg);
    root.selectAll("*").remove();

    const g = root
      .append("g")
      .attr("transform", `translate(${WIDTH / 2},${HEIGHT / 2})`);

    const defs = root.append("defs");
    defs
      .append("marker")
      .attr("id", "arrow-seed")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 18)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L10,0L0,4")
      .attr("fill", "#3a474f");
    defs
      .append("marker")
      .attr("id", "arrow-adopt")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 18)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L10,0L0,4")
      .attr("fill", "#58d7c1");
    defs
      .append("marker")
      .attr("id", "arrow-seal")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 18)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L10,0L0,4")
      .attr("fill", "#ff5d5d");

    const simulation = d3
      .forceSimulation<GNode>(nodes)
      .force(
        "link",
        d3
          .forceLink<GNode, GLink>(links)
          .id((d) => d.id)
          .distance((l) => (l.kind === "seal" ? 60 : l.kind === "adopt" ? 110 : 140))
          .strength((l) => (l.kind === "fork" ? 0.55 : 0.2)),
      )
      .force("charge", d3.forceManyBody<GNode>().strength(-420))
      .force("collide", d3.forceCollide<GNode>().radius(52))
      .force("x", d3.forceX(0).strength(0.08))
      .force("y", d3.forceY(0).strength(0.08));

    const link = g
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "lg-link")
      .attr("stroke", (l) =>
        l.kind === "fork" ? "#3a474f" : l.kind === "adopt" ? "#58d7c1" : "#ff5d5d",
      )
      .attr("stroke-dasharray", (l) =>
        l.kind === "fork" ? null : l.kind === "adopt" ? "5 4" : "2 4",
      )
      .attr("stroke-opacity", 0.75)
      .attr("marker-end", (l) =>
        l.kind === "fork"
          ? "url(#arrow-seed)"
          : l.kind === "adopt"
            ? "url(#arrow-adopt)"
            : "url(#arrow-seal)",
      );

    const nodeG = g
      .append("g")
      .selectAll<SVGGElement, GNode>("g")
      .data(nodes)
      .join("g")
      .attr("class", "lg-node")
      .attr("cursor", "pointer")
      .on("click", (_e, d) => onSelectRef.current(d.id));

    const circle = nodeG
      .append("circle")
      .attr("r", 26)
      .attr("fill", (d) => {
        if (d.sealed) return "#1a2024";
        return d.source === "local" ? "#3a2d18" : "#102028";
      })
      .attr("stroke", (d) => {
        if (d.sealed) return "#3a474f";
        if (d.id === selectedId) return "#ffb454";
        return d.source === "local" ? "#ffb454" : "#58d7c1";
      })
      .attr("stroke-width", (d) => (d.id === selectedId ? 3 : 1.5))
      .attr("stroke-dasharray", (d) => (d.sealed ? "3 3" : null));
    void circle;

    nodeG
      .append("circle")
      .attr("r", 31)
      .attr("fill", "none")
      .attr("stroke", "#ffb454")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "2 3")
      .attr("opacity", (d) => (d.id === myId ? 1 : 0));

    nodeG
      .append("text")
      .attr("dy", -34)
      .attr("text-anchor", "middle")
      .attr("class", "lg-name")
      .attr("text-decoration", (d) => (d.sealed ? "line-through" : null))
      .attr("fill", (d) => (d.sealed ? "#3a474f" : d.source === "local" ? "#ffb454" : "#58d7c1"))
      .text((d) => d.name);

    nodeG
      .append("text")
      .attr("dy", 4)
      .attr("text-anchor", "middle")
      .attr("class", "lg-id")
      .text((d) => (d.sealed ? "VANISHED" : d.id.slice(2, 10)));

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as GNode).x ?? 0)
        .attr("y1", (d) => (d.source as GNode).y ?? 0)
        .attr("x2", (d) => (d.target as GNode).x ?? 0)
        .attr("y2", (d) => (d.target as GNode).y ?? 0);
      nodeG.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    // drag
    nodeG.call(
      d3
        .drag<SVGGElement, GNode>()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }),
    );

    return () => {
      simulation.stop();
    };
  }, [network, selectedId, myId]);

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="lineage-svg"
    />
  );
}
