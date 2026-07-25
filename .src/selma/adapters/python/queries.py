"""Tree-sitter query strings for Python parsing."""

FUNCTION_QUERY = """
(function_definition
  name: (identifier) @func_name
  parameters: (parameters) @params
  body: (block) @body
) @func_def
"""

DECORATOR_QUERY = """
(decorated_definition
  (decorator) @decorator
  definition: (function_definition) @func_def
) @decorated
"""

CLASS_QUERY = """
(class_definition
  name: (identifier) @class_name
  body: (block) @body
) @class_def
"""

IMPORT_QUERY = """
(import_statement
  (dotted_name) @module
) @import

(import_from_statement
  (dotted_name) @module
) @import_from
"""

PARAMETER_QUERY = """
(identifier) @param_name
"""
