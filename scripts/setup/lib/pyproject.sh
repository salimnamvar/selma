#!/usr/bin/env bash
# Parse pyproject.toml (no python dep) — adapted for nasim.

if [[ -n "${SETUP_PYPROJECT_SH:-}" ]]; then return 0 2>/dev/null || exit 0; fi
SETUP_PYPROJECT_SH=1

PYPROJECT_PATH="${PROJECT_ROOT}/pyproject.toml"

_parse_pyproject_toml() {
  local file="$1"
  [[ -f "${file}" ]] || die "pyproject.toml not found: ${file}"

  local output
  output="$(
    awk '
      function trim(s){sub(/^[ \t]+/,"",s);sub(/[ \t]+$/,"",s);return s}
      function unquote(s){
        if(s~/^".*"$/){sub(/^"/,"",s);sub(/"$/,"",s)}
        else if(s~/^'\''.*'\''$/){sub(/^'\''/,"",s);sub(/'\''$/,"",s)}
        return s
      }
      function strip_comment(s){
        if(match(s,/[ \t]#/)) s=substr(s,1,RSTART-1); return trim(s)
      }
      function emit(k,v){ gsub(/\\/,"\\\\",v); gsub(/"/,"\\\"",v); printf "%s=\"%s\"\n",k,v }

      BEGIN { section=""; in_dev=0 }
      /^[ \t]*#/ { next }
      /^[ \t]*$/ { next }

      /^\[/ {
        line=$0; gsub(/^[ \t]*\[/,"",line); gsub(/\][ \t]*$/,"",line)
        section=line; in_dev=0; next
      }

      {
        line=$0; sub(/^[ \t]+/,"",line)
        if(section=="project" && match(line,/^name[ \t]*=[ \t]*/)){
          emit("PROJECT_NAME", unquote(strip_comment(substr(line,RSTART+RLENGTH)))); next
        }
        if(section=="project" && match(line,/^requires-python[ \t]*=[ \t]*/)){
          emit("PROJECT_REQUIRES_PYTHON", unquote(strip_comment(substr(line,RSTART+RLENGTH)))); next
        }
        if(section=="project.optional-dependencies"){
          if(match(line,/^dev[ \t]*=[ \t]*\[/)){ emit("PROJECT_HAS_DEV_EXTRAS","1"); in_dev=1; next }
          if(in_dev){ if(line ~ /\]/) in_dev=0; next }
        }
        if(section=="tool.black" && match(line,/^line-length[ \t]*=[ \t]*/)){
          emit("BLACK_LINE_LENGTH", unquote(strip_comment(substr(line,RSTART+RLENGTH)))); next
        }
        if(section=="tool.ruff" && match(line,/^line-length[ \t]*=[ \t]*/)){
          emit("RUFF_LINE_LENGTH", unquote(strip_comment(substr(line,RSTART+RLENGTH)))); next
        }
        if(section=="tool.isort" && match(line,/^profile[ \t]*=[ \t]*/)){
          emit("ISORT_PROFILE", unquote(strip_comment(substr(line,RSTART+RLENGTH)))); next
        }
        if(section=="tool.isort" && match(line,/^line_length[ \t]*=[ \t]*/)){
          emit("ISORT_LINE_LENGTH", unquote(strip_comment(substr(line,RSTART+RLENGTH)))); next
        }
        if(section=="tool.pytest.ini_options" && match(line,/^testpaths[ \t]*=[ \t]*\[/)){
          v=substr(line,RSTART+RLENGTH); sub(/\].*$/,"",v); emit("PYTEST_TESTPATHS", unquote(strip_comment(v))); next
        }
      }
    ' "${file}"
  )"
  eval "${output}"
}

_extract_python_version() {
  local spec="$1"
  [[ "$spec" =~ ([0-9]+\.[0-9]+) ]] && printf '%s' "${BASH_REMATCH[1]}" || die "bad requires-python: $spec"
}

_sanitize_env_name() {
  local n="${1,,}"; n="${n//-/_}"; n="${n//./_}"; printf '%s' "$n"
}

load_pyproject_config() {
  _parse_pyproject_toml "${PYPROJECT_PATH}"

  [[ -n "${PROJECT_NAME:-}" ]] || PROJECT_NAME="nasim"
  [[ -n "${PROJECT_REQUIRES_PYTHON:-}" ]] || PROJECT_REQUIRES_PYTHON=">=3.10"

  PYTHON_VERSION="$(_extract_python_version "${PROJECT_REQUIRES_PYTHON}")"
  ENV_NAME="$(_sanitize_env_name "${PROJECT_NAME}")"

  # defaults if not parsed
  : "${BLACK_LINE_LENGTH:=120}"
  : "${RUFF_LINE_LENGTH:=120}"
  : "${ISORT_PROFILE:=google}"
  : "${ISORT_LINE_LENGTH:=120}"
  : "${PYTEST_TESTPATHS:=tests}"
  : "${PYTHON_ANALYSIS_PATHS:=nasim}"
  : "${TERMINAL_PROFILE_NAME:=${ENV_NAME} (conda)}"
  : "${PROJECT_HAS_DEV_EXTRAS:=1}"
  : "${PIP_INSTALL_TARGET:=.}"

  CONDA_BIN="${CONDA_DIR}/bin/conda"
}
