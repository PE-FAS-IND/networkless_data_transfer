global node_mode

print(node_mode)

if node_mode=='gateway':
    import fdt_gateway
elif node_mode=='node':
    import fdt_node
else:   
    print(f"Unsupported node mode: {node_mode}")
