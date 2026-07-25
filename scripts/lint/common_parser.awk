#!/usr/bin/env awk -f
# common_parser.awk
# Shared parsing logic for Arian Python linters

function calc_indent(line,    _t) {
    if (line ~ /^[[:space:]]*$/) return -1
    _t = line
    gsub(/[^[:space:]].*$/, "", _t)
    return length(_t)
}

function strip_code(line,    result, i, len, c, in_str, in_tq_str, quote) {
    result = ""
    in_str = 0
    in_tq_str = 0
    quote = ""

    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)

        if (!in_tq_str && i+2 <= length(line)) {
            tq = substr(line, i, 3)
            if (tq == "\"\"\"" || tq == "'''") {
                in_tq_str = 1
                quote = substr(tq, 1, 1)
                result = result "   "
                i += 2
                continue
            }
        } else if (in_tq_str && i+2 <= length(line)) {
            tq = substr(line, i, 3)
            if (tq == quote quote quote) {
                in_tq_str = 0
                result = result "   "
                i += 2
                continue
            }
        }

        if (in_str) {
            if (c == quote) {
                if (i > 1 && substr(line, i-1, 1) == "\\") {
                    result = result c
                    continue
                }
                in_str = 0
                result = result " "
            } else {
                result = result " "
            }
            continue
        }

        if (c == "\"" || c == "'") {
            in_str = 1
            quote = c
            result = result " "
            continue
        }

        if (c == "#" && !in_str && !in_tq_str) {
            break
        }

        result = result c
    }
    return result
}
