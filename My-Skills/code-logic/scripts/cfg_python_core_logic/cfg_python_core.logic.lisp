(flow-graph :name "python_cfg"
  (nodes
    (block  :id block_1    :label "def __init__")
    (exit   :id exit_2     :label "return/exit")
    (block  :id block_3    :label "self.code = code_bytes")
    (block  :id block_4    :label "self.graph = UniversalLogicGraph(\"pyt...")
    (block  :id block_5    :label "self.loop_stack = []")
    (block  :id block_6    :label "self.fn_exit = None")
    (block  :id block_7    :label "self.config_loader = None")
  )
  (edges
    (seq      block_1 -> block_3)
    (seq      block_3 -> block_4)
    (seq      block_4 -> block_5)
    (seq      block_5 -> block_6)
    (seq      block_6 -> block_7)
    (seq      block_7 -> exit_2)
  )
)