global node_mode
print(f"Start in {node_mode}")
if node_mode=='gateway':
    import nldt_gateway
elif node_mode=='node':
    import nldt_node
else:   
    print(f"Unsupported node mode: {node_mode}")
