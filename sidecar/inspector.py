"""Schematic inspection utilities for analyzing KiCad schematics including hierarchical sheets."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from skip.eeschema import schematic as sch
import re


def inspect_schematic(sch_path: Path) -> Dict:
    """
    Inspect a KiCad schematic file and return comprehensive information.
    
    Returns dictionary with:
    - components: List of component info (ref, value, symbol, position)
    - nets: List of net names
    - labels: List of net labels with positions
    - hierarchy: List of hierarchical sheets (if any)
    - stats: Statistics about the schematic
    """
    try:
        doc = sch.Schematic(str(sch_path))
        
        # Get components
        components = []
        for sym in doc.symbol:
            try:
                # Use the same helper function as writer_skip.py
                from sidecar.writer_skip import get_symbol_ref
                ref = get_symbol_ref(sym)
                if not ref:
                    continue
                    
                # Try to get value - check various attributes
                value = "N/A"
                if hasattr(sym, 'allValues') and sym.allValues:
                    value = str(sym.allValues[0]).split('=')[-1].strip() if '=' in str(sym.allValues[0]) else str(sym.allValues[0]).strip()
                
                # Get position if available
                pos = (0, 0)
                if hasattr(sym, 'at') and sym.at:
                    pos = (sym.at.x if hasattr(sym.at, 'x') else 0, 
                           sym.at.y if hasattr(sym.at, 'y') else 0)
                
                # Get lib_id
                lib_id = str(sym.libId) if hasattr(sym, 'libId') else "Unknown"
                
                components.append({
                    "ref": ref,
                    "value": value,
                    "symbol": lib_id,
                    "position": pos
                })
            except Exception as e:
                # Skip symbols that can't be read
                continue
        
        # Get nets - simplified, just extract from labels and wires
        nets = []
        try:
            # Get labels which represent nets
            if hasattr(doc, 'labels'):
                for label in doc.labels():
                    label_text = str(label.text) if hasattr(label, 'text') else str(label)
                    if label_text and label_text not in nets:
                        nets.append(label_text)
        except Exception:
            nets = []
        
        # Get labels
        labels = []
        try:
            if hasattr(doc, 'labels'):
                for label in doc.labels():
                    label_text = str(label.text) if hasattr(label, 'text') else str(label)
                    pos = (0, 0)
                    if hasattr(label, 'at') and label.at:
                        pos = (label.at.x if hasattr(label.at, 'x') else 0,
                               label.at.y if hasattr(label.at, 'y') else 0)
                    labels.append({
                        "text": label_text,
                        "position": pos
                    })
        except Exception:
            labels = []
        
        # Get hierarchical sheets - simplified
        hierarchy = []
        try:
            if hasattr(doc, 'sheetInstances'):
                for sheet in doc.sheetInstances:
                    # Extract basic sheet info
                    sheet_name = str(sheet.path) if hasattr(sheet, 'path') else "Unnamed"
                    hierarchy.append({
                        "name": sheet_name,
                        "file": None,  # Not easily accessible
                        "position": (0, 0)
                    })
        except Exception:
            # If sheets aren't supported or don't exist
            hierarchy = []
        
        # Calculate statistics
        stats = {
            "total_components": len(components),
            "total_nets": len(nets),
            "total_labels": len(labels),
            "total_sheets": len(hierarchy),
            "component_types": {}
        }
        
        # Count component types
        for comp in components:
            ref_type = ''.join([c for c in comp["ref"] if c.isalpha()])
            stats["component_types"][ref_type] = stats["component_types"].get(ref_type, 0) + 1
        
        return {
            "success": True,
            "file": str(sch_path),
            "components": components,
            "nets": nets,
            "labels": labels,
            "hierarchy": hierarchy,
            "stats": stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file": str(sch_path)
        }


def format_inspection_report(inspection: Dict) -> str:
    """Format inspection results as a human-readable report."""
    if not inspection.get("success"):
        return f"❌ Failed to inspect schematic: {inspection.get('error', 'Unknown error')}"
    
    report = []
    report.append(f"📊 **Schematic Inspection Report**")
    report.append(f"File: {Path(inspection['file']).name}")
    report.append("")
    
    stats = inspection.get("stats", {})
    report.append("**Statistics:**")
    report.append(f"  • Components: {stats.get('total_components', 0)}")
    report.append(f"  • Nets: {stats.get('total_nets', 0)}")
    report.append(f"  • Labels: {stats.get('total_labels', 0)}")
    report.append(f"  • Hierarchical Sheets: {stats.get('total_sheets', 0)}")
    report.append("")
    
    # Component breakdown
    if stats.get("component_types"):
        report.append("**Component Types:**")
        for comp_type, count in sorted(stats["component_types"].items()):
            report.append(f"  • {comp_type}: {count}")
        report.append("")
    
    # Hierarchical sheets
    if inspection.get("hierarchy"):
        report.append("**Hierarchical Sheets:**")
        for sheet in inspection["hierarchy"]:
            report.append(f"  • {sheet['name']}")
            if sheet.get('file'):
                report.append(f"    File: {sheet['file']}")
            report.append(f"    Position: {sheet['position']}")
        report.append("")
    
    # List components
    components = inspection.get("components", [])
    if components:
        report.append(f"**Components ({len(components)}):**")
        for comp in sorted(components, key=lambda x: x['ref'])[:20]:  # Limit to first 20
            report.append(f"  • {comp['ref']}: {comp['value']} ({comp['symbol']})")
        if len(components) > 20:
            report.append(f"  ... and {len(components) - 20} more")
        report.append("")
    
    # List nets
    nets = inspection.get("nets", [])
    if nets:
        report.append(f"**Nets ({len(nets)}):**")
        for net in sorted(nets)[:15]:  # Limit to first 15
            report.append(f"  • {net}")
        if len(nets) > 15:
            report.append(f"  ... and {len(nets) - 15} more")
    
    return "\n".join(report)


def inspect_hierarchical_design(root_sch_path: Path) -> Dict:
    """
    Inspect a hierarchical design starting from the root schematic.
    
    Returns information about the root sheet and all sub-sheets.
    """
    results = {
        "root": inspect_schematic(root_sch_path),
        "subsheets": {}
    }
    
    # If the root has hierarchical sheets, try to inspect them
    if results["root"].get("hierarchy"):
        root_dir = root_sch_path.parent
        for sheet in results["root"]["hierarchy"]:
            sheet_file = sheet.get("file")
            if sheet_file:
                sheet_path = root_dir / sheet_file
                if sheet_path.exists():
                    results["subsheets"][sheet["name"]] = inspect_schematic(sheet_path)
                else:
                    results["subsheets"][sheet["name"]] = {
                        "success": False,
                        "error": f"Sheet file not found: {sheet_file}"
                    }
    
    return results


def find_component_by_reference(sch_path: Path, ref: str) -> Optional[Dict]:
    """
    Find a specific component by its reference designator (e.g., C2, R47, U1).
    
    Returns detailed component information including:
    - Reference, value, symbol
    - Position and rotation
    - Connected nets/pins
    - Additional fields
    """
    try:
        doc = sch.Schematic(str(sch_path))
        
        # Search for the component
        for sym in doc.symbol:
            try:
                sym_ref = sym.ref()
                if sym_ref.upper() == ref.upper():
                    # Found it! Get detailed info
                    info = {
                        "ref": sym_ref,
                        "value": sym.value() if hasattr(sym, 'value') else "N/A",
                        "symbol": sym.lib_id() if hasattr(sym, 'lib_id') else "Unknown",
                        "position": sym.pos() if hasattr(sym, 'pos') else (0, 0),
                        "rotation": sym.rotation() if hasattr(sym, 'rotation') else 0,
                        "pins": [],
                        "fields": {}
                    }
                    
                    # Get pins
                    try:
                        if hasattr(sym, 'pins'):
                            for pin in sym.pins():
                                pin_info = {
                                    "number": pin.number() if hasattr(pin, 'number') else "?",
                                    "name": pin.name() if hasattr(pin, 'name') else "?",
                                    "type": pin.type() if hasattr(pin, 'type') else "?"
                                }
                                info["pins"].append(pin_info)
                    except Exception:
                        pass
                    
                    # Get additional fields
                    try:
                        if hasattr(sym, 'fields'):
                            for field in sym.fields():
                                field_name = field.name() if hasattr(field, 'name') else str(field)
                                field_value = field.value() if hasattr(field, 'value') else str(field)
                                info["fields"][field_name] = field_value
                    except Exception:
                        pass
                    
                    return info
            except Exception:
                continue
        
        return {"success": False, "error": f"Component {ref} not found"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_components_by_pattern(sch_path: Path, pattern: str) -> List[Dict]:
    """
    Find all components matching a pattern (e.g., "C*", "R4*", "U[1-3]").
    
    Returns list of matching components with basic info.
    """
    try:
        doc = sch.Schematic(str(sch_path))
        matches = []
        
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex = re.compile(regex_pattern, re.IGNORECASE)
        
        for sym in doc.symbol:
            try:
                sym_ref = sym.ref()
                if regex.match(sym_ref):
                    matches.append({
                        "ref": sym_ref,
                        "value": sym.value() if hasattr(sym, 'value') else "N/A",
                        "symbol": sym.lib_id() if hasattr(sym, 'lib_id') else "Unknown",
                        "position": sym.pos() if hasattr(sym, 'pos') else (0, 0)
                    })
            except Exception:
                continue
        
        return sorted(matches, key=lambda x: x['ref'])
        
    except Exception as e:
        return [{"error": str(e)}]


def inspect_net_connections(sch_path: Path, net_name: str) -> Dict:
    """
    Inspect a specific net and find all components/pins connected to it.
    
    Returns:
    - Net name
    - List of connected components (ref, pin, position)
    - Net class/properties if available
    """
    try:
        doc = sch.Schematic(str(sch_path))
        
        connections = []
        labels_on_net = []
        
        # Try to find the net and its connections
        try:
            for net in doc.nets():
                if hasattr(net, 'name') and net.name() == net_name:
                    # Found the net, now find connected components
                    # This depends on the skip library API
                    if hasattr(net, 'items') or hasattr(net, 'connections'):
                        items = net.items() if hasattr(net, 'items') else net.connections()
                        for item in items:
                            try:
                                connections.append({
                                    "type": type(item).__name__,
                                    "info": str(item)
                                })
                            except Exception:
                                pass
        except Exception:
            pass
        
        # Find labels with this net name
        try:
            for label in doc.labels():
                label_text = label.text() if hasattr(label, 'text') else str(label)
                if label_text == net_name:
                    labels_on_net.append({
                        "text": label_text,
                        "position": label.pos() if hasattr(label, 'pos') else (0, 0)
                    })
        except Exception:
            pass
        
        return {
            "success": True,
            "net_name": net_name,
            "connections": connections,
            "labels": labels_on_net,
            "connection_count": len(connections)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "net_name": net_name
        }


def get_component_connections(sch_path: Path, ref: str) -> Dict:
    """
    Get all net connections for a specific component.
    
    Returns component info plus all connected nets per pin.
    """
    try:
        doc = sch.Schematic(str(sch_path))
        
        # Find the component first
        component_info = find_component_by_reference(sch_path, ref)
        if not component_info:
            return {
                "success": False,
                "error": f"Component {ref} not found"
            }
        
        # Try to find what nets are connected to each pin
        # This is complex and depends on the schematic structure
        pin_connections = {}
        
        # Get all labels that might be near this component
        try:
            comp_pos = component_info.get("position", (0, 0))
            nearby_labels = []
            
            for label in doc.labels():
                label_pos = label.pos() if hasattr(label, 'pos') else (0, 0)
                # Check if label is near component (within 20mm)
                distance = ((comp_pos[0] - label_pos[0])**2 + (comp_pos[1] - label_pos[1])**2)**0.5
                if distance < 20:
                    nearby_labels.append({
                        "text": label.text() if hasattr(label, 'text') else str(label),
                        "position": label_pos,
                        "distance": distance
                    })
            
            component_info["nearby_nets"] = nearby_labels
        except Exception:
            pass
        
        return {
            "success": True,
            "component": component_info,
            "pin_connections": pin_connections
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ref": ref
        }


def search_components(sch_path: Path, search_term: str) -> List[Dict]:
    """
    Search for components by reference, value, or symbol name.
    
    Returns list of matching components.
    """
    try:
        doc = sch.Schematic(str(sch_path))
        matches = []
        search_lower = search_term.lower()
        
        for sym in doc.symbol:
            try:
                sym_ref = sym.ref()
                sym_value = sym.value() if hasattr(sym, 'value') else ""
                sym_lib = sym.lib_id() if hasattr(sym, 'lib_id') else ""
                
                # Check if search term matches ref, value, or symbol
                if (search_lower in sym_ref.lower() or 
                    search_lower in str(sym_value).lower() or 
                    search_lower in str(sym_lib).lower()):
                    
                    matches.append({
                        "ref": sym_ref,
                        "value": sym_value,
                        "symbol": sym_lib,
                        "position": sym.pos() if hasattr(sym, 'pos') else (0, 0)
                    })
            except Exception:
                continue
        
        return matches
        
    except Exception as e:
        return [{"error": str(e)}]
