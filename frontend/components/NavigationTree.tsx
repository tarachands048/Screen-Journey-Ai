"use client";
import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { TreeNode } from "@/types";

interface Props {
  tree: TreeNode;
  onNodeClick?: (node: TreeNode) => void;
}

export default function NavigationTree({ tree, onNodeClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !tree) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth || 600;
    const height = 400;
    const margin = { top: 20, right: 120, bottom: 20, left: 80 };

    const root = d3.hierarchy(tree, (d) => d.children);
    const treeLayout = d3.tree<TreeNode>().size([height - margin.top - margin.bottom, width - margin.left - margin.right]);
    treeLayout(root);

    const g = svg
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Links
    g.selectAll(".link")
      .data(root.links())
      .join("path")
      .attr("class", "link")
      .attr("d", d3.linkHorizontal<any, any>().x((d) => d.y).y((d) => d.x))
      .attr("fill", "none")
      .attr("stroke", (d) => (d.target.data.is_backtrack_destination ? "#f59e0b" : "#6366f1"))
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.6);

    // Nodes
    const node = g
      .selectAll(".node")
      .data(root.descendants())
      .join("g")
      .attr("class", "node")
      .attr("transform", (d) => `translate(${d.y},${d.x})`)
      .style("cursor", "pointer")
      .on("click", (_, d) => onNodeClick?.(d.data));

    node
      .append("circle")
      .attr("r", 6)
      .attr("fill", (d) => (d.data.is_backtrack_destination ? "#f59e0b" : d.depth === 0 ? "#6366f1" : "#818cf8"))
      .attr("stroke", "var(--background)")
      .attr("stroke-width", 2);

    node
      .append("text")
      .attr("dy", "0.31em")
      .attr("x", (d) => (d.children ? -10 : 10))
      .attr("text-anchor", (d) => (d.children ? "end" : "start"))
      .attr("font-size", "11px")
      .attr("fill", "currentColor")
      .text((d) => {
        const title = d.data.title || "Page";
        return title.length > 20 ? title.slice(0, 20) + "…" : title;
      });

    // Tooltip on hover
    node.append("title").text((d) => `${d.data.title}\nTime: ${d.data.time_spent}s\nVisits: ${d.data.visit_count}`);
  }, [tree, onNodeClick]);

  return (
    <div className="w-full overflow-x-auto">
      <svg ref={svgRef} className="w-full" style={{ minHeight: 400 }} />
    </div>
  );
}
