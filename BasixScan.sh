#!/bin/bash
set -o pipefail
IFS=$'\n'
PROXY_IP="157.240.195.32"
PROXY_PORT=8080
MAX_JOBS=40
SOCKET_TIMEOUT=20
RECV_TIMEOUT=5
ALL_PROXIES=(
"31.13.94.39" "31.13.84.39" "157.240.8.39" "179.60.195.39" "157.240.9.39"
"157.240.234.38" "157.240.222.32" "31.13.85.39" "157.240.226.38" "157.240.12.39"
"31.13.90.36" "31.13.80.39" "157.240.17.32" "157.240.204.32" "163.70.152.41"
"57.144.114.4" "157.240.30.39" "185.60.217.39" "157.240.27.39" "57.144.248.4"
"57.144.244.4" "157.240.0.38" "157.240.253.39" "157.240.210.32" "157.240.223.32"
"157.240.200.32" "102.132.97.39" "102.132.103.36" "157.240.243.39" "31.13.83.39"
"157.240.5.32" "157.240.205.37" "157.240.195.32" "157.240.196.32" "185.60.219.38"
"157.240.202.37" "163.70.128.38" "57.144.238.4" "57.144.240.4" "163.70.151.38"
"157.240.214.38" "157.240.225.38" "157.240.233.38" "157.240.199.32" "157.240.211.38"
"57.144.100.4" "157.240.208.32" "31.13.95.38" "31.13.73.38" "157.240.23.37"
"157.240.192.32" "163.70.146.39" "163.70.140.41" "157.240.1.38" "31.13.64.39"
"157.240.16.38" "157.240.242.39" "163.70.144.33" "157.240.237.39" "57.144.124.4"
"157.240.198.32" "157.240.239.38" "31.13.86.39" "31.13.69.38" "157.240.231.38"
"157.240.209.32" "31.13.82.39" "31.13.76.32" "157.240.215.32" "157.240.244.39"
"31.13.89.37" "157.240.25.38" "157.240.236.36" "163.70.132.41" "163.70.137.39"
"102.132.101.38" "57.144.222.4" "157.240.201.32" "31.13.78.37" "157.240.227.38"
"157.240.197.32" "163.70.130.39" "57.144.110.4" "157.240.212.32" "157.240.29.36"
"185.60.218.39" "31.13.72.39" "57.144.152.4" "57.144.14.4" "57.144.160.4"
"157.240.13.39" "157.240.15.38" "163.70.148.33" "163.70.149.42" "57.144.126.4"
"31.13.87.39" "157.240.224.39" "31.13.66.32" "157.240.229.38" "57.144.22.4"
"157.240.14.38" "57.144.204.4" "157.240.254.39" "57.144.218.4" "31.13.93.37"
"57.144.104.4" "157.240.24.37" "57.144.252.4" "31.13.88.38" "31.13.70.39"
"157.240.11.39" "157.240.26.39" "57.144.116.4" "57.144.102.4" "157.240.22.38"
"157.240.3.39" "31.13.71.39" "157.240.241.38" "157.240.245.39" "102.132.99.38"
"102.132.104.41"
)
C200="\033[38;5;40m"
C403="\033[38;5;203m"
C429="\033[38;5;214m"
C502="\033[38;5;141m"
C_OTHER="\033[38;5;245m"
CTITLE="\033[38;5;39m"
CMENU="\033[38;5;45m"
CPROMPT="\033[38;5;51m"
CSTATUS="\033[38;5;228m"
CHOST="\033[38;5;117m"
CRESET="\033[0m"
BOLD="\033[1m"
now_ts(){ date +"%Y%m%d_%H%M%S"; }
clear_screen(){
  command -v clear >/dev/null 2>&1 && clear || printf "\n%.0s" {1..4}
}
print_banner(){
  clear_screen
  W=54
  printf "%b%s%b\n" "$CTITLE$BOLD" "$(printf '+%*s+' "$W" '' | sed 's/ /-/g' )" "$CRESET"
  printf "%b|%*s|%b\n" "$CTITLE" $(( (W+${#title:=FreeBasics Checker})/2 )) "$title" "$CRESET"
  printf "%b|%*s|%b\n" "$CTITLE" $(( (W+${#dev:="Developed by: FirewallFalcon"})/2 )) "$dev" "$CRESET"
  printf "%b%s%b\n\n" "$CTITLE" "$(printf '+%*s+' "$W" '' | sed 's/ /-/g' )" "$CRESET"
}
send_connect(){
  local proxy_ip="$1"; local proxy_port="$2"; local target="$3"; local tport="${4:-443}"
  local payload
  payload=$(
    printf "CONNECT %s:%s HTTP/1.1\r\n" "$target" "$tport"
    printf "Host: %s:%s\r\n" "$target" "$tport"
    printf "Proxy-Connection: keep-alive\r\n"
    printf "User-Agent: Mozilla/5.0 (Linux; Android 14; SM-A245F) Chrome/133.0.6943.122 [FBAN/InternetOrgApp;FBAV/166.0.0.0.169;]\r\n"
    printf "X-IORG-BSID: a08359b0-d7ec-4cb5-97bf-000bdc29ec87\r\n"
    printf "X-IORG-SERVICE-ID: null\r\n\r\n"
  )
  local resp
  resp=$(timeout "${SOCKET_TIMEOUT}" bash -c '
    exec 3<>/dev/tcp/'"$proxy_ip"'/'"$proxy_port"' 2>/dev/null || { echo "[ERROR] connect_failed"; exit 0; }
    printf "%s" "'"$payload"'" >&3 2>/dev/null || { echo "[ERROR] send_failed"; exec 3>&-; exit 0; }
    local buf=""
    while IFS= read -r -t '"$RECV_TIMEOUT"' line <&3; do
      printf "%s\n" "$line"
    done
    exec 3>&-
  ')
  if [ -z "$resp" ]; then
    echo "[ERROR] no_response_or_timeout"
  else
    echo "$resp"
  fi
}
categorize(){
  local r="$1"
  if printf "%s" "$r" | grep -q " 200 "; then
    echo "200 OK"
  elif printf "%s" "$r" | grep -q " 403 "; then
    echo "403 Forbidden"
  elif printf "%s" "$r" | grep -q " 429 "; then
    echo "429 Too Many Requests"
  elif printf "%s" "$r" | grep -q " 502 "; then
    echo "502 Bad Gateway"
  elif printf "%s" "$r" | grep -q "^\[ERROR\]"; then
    echo "Others"
  else
    echo "Others"
  fi
}
color_for(){
  case "$1" in
    "200 OK") echo -n "$C200";;
    "403 Forbidden") echo -n "$C403";;
    "429 Too Many Requests") echo -n "$C429";;
    "502 Bad Gateway") echo -n "$C502";;
    *) echo -n "$C_OTHER";;
  esac
}
print_summary(){
  declare -n _sum=$1
  printf "\n%b%bSUMMARY:%b\n" "$CSTATUS" "$BOLD" "$CRESET"
  for k in "200 OK" "403 Forbidden" "429 Too Many Requests" "502 Bad Gateway" "Others"; do
    printf "  %b%-22s%b : %s\n" "$(color_for "$k")" "$k" "$CRESET" "${_sum[$k]:-0}"
  done
}
mode_single_host(){
  read -rp $'\n'"Enter host: " host
  [ -z "$host" ] && { echo "No host"; return; }
  echo -e "\n${CHOST}Checking: $host${CRESET}"
  resp=$(send_connect "$PROXY_IP" "$PROXY_PORT" "$host")
  status=$(categorize "$resp")
  echo -e "\n${CSTATUS}Status:${CRESET} $(color_for "$status")$status${CRESET}"
  echo -e "${BOLD}Response:${CRESET}\n$resp"
  echo -e "${C_OTHER}────────────────────────${CRESET}"
}
mode_multiple_hosts(){
  echo -e "\n${CPROMPT}Enter hosts (one per line). Type 'done' when finished or leave empty to cancel:${CRESET}"
  hosts=()
  while read -r line; do
    [ "$line" = "done" ] && break
    [ -z "$line" ] && continue
    hosts+=( "$line" )
  done
  if [ ${#hosts[@]} -eq 0 ]; then
    echo -e "${CPROMPT}No hosts entered. To load from a file, choose option 3 in main menu.${CRESET}"
    return
  fi
  echo -e "\n${BOLD}Scanning ${#hosts[@]} hosts via ${PROXY_IP}:${PROXY_PORT}...${CRESET}"
  declare -A summary
  summary=( ["200 OK"]=0 ["403 Forbidden"]=0 ["429 Too Many Requests"]=0 ["502 Bad Gateway"]=0 ["Others"]=0 )
  results=()
  hosts_200=(); hosts_403=(); hosts_429=(); hosts_502=(); hosts_others=()
  running=0
  for h in "${hosts[@]}"; do
    while [ "$(jobs -rp | wc -l)" -ge "$MAX_JOBS" ]; do sleep 0.08; done
    {
      resp=$(send_connect "$PROXY_IP" "$PROXY_PORT" "$h")
      status=$(categorize "$resp")
      printf "%s\n" "$status|$h|$resp" > /tmp/fb_result_$$_"$RANDOM"
    } &
  done
  wait
  for f in /tmp/fb_result_$$_*; do
    [ -f "$f" ] || continue
    IFS='|' read -r status host resp < <(sed -n '1p' "$f")
    rest=$(sed -n '2,$p' "$f")
    summary["$status"]=$((summary["$status"] + 1))
    case "$status" in
      "200 OK") hosts_200+=( "$host" ) ;;
      "403 Forbidden") hosts_403+=( "$host" ) ;;
      "429 Too Many Requests") hosts_429+=( "$host" ) ;;
      "502 Bad Gateway") hosts_502+=( "$host" ) ;;
      *) hosts_others+=( "$host" ) ;;
    esac
    results+=( "$status → $host"$'\n'"$rest"$'\n'"════════════════════════════════════════════════════════════════════════' )
    printf "%b[%d/%d] Checking:%b %s\n" "$CHOST" "${#results}" "${#hosts[@]}" "$CRESET" "$host"
    printf "  %bStatus:%b %s\n" "$CSTATUS" "$CRESET" "$(color_for "$status")$status${CRESET}"
    print_summary summary
    printf "%b%s%b\n" "$C_OTHER" "$(printf '─%.0s' {1..60})" "$CRESET"
    rm -f "$f"
  done
  ts=$(now_ts)
  grouped_file="hosts_grouped_${ts}.txt"
  {
    echo "200 OK hosts"
    if [ ${#hosts_200[@]} -gt 0 ]; then for x in "${hosts_200[@]}"; do echo "$x"; done; else echo "(None)"; fi
    echo; echo "429 Too Many Requests hosts"
    if [ ${#hosts_429[@]} -gt 0 ]; then for x in "${hosts_429[@]}"; do echo "$x"; done; else echo "(None)"; fi
    echo; echo "502 Bad Gateway hosts"
    if [ ${#hosts_502[@]} -gt 0 ]; then for x in "${hosts_502[@]}"; do echo "$x"; done; else echo "(None)"; fi
    echo; echo "Others hosts"
    if [ ${#hosts_others[@]} -gt 0 ]; then for x in "${hosts_others[@]}"; do echo "$x"; done; else echo "(None)"; fi
    echo; echo "403 Forbidden hosts"
    if [ ${#hosts_403[@]} -gt 0 ]; then for x in "${hosts_403[@]}"; do echo "$x"; done; else echo "(None)"; fi
  } > "$grouped_file"
  echo -e "${C200}Saved grouped hosts to ${grouped_file}${CRESET}"
  raw_file="scan_results_${ts}.txt"
  printf "%s\n" "${results[@]}" > "$raw_file"
  echo -e "${C200}Saved raw results to ${raw_file}${CRESET}"
}
mode_single_host_all_proxies(){
  read -rp $'\n'"Enter target host to test through all proxies: " host
  [ -z "$host" ] && { echo "No host"; return; }
  echo -e "\n${BOLD}Scanning host '$host' through ${#ALL_PROXIES[@]} proxies (port 8080)...${CRESET}"
  ts=$(now_ts)
  grouped_file="proxy_scan_grouped_${host}_${ts}.txt"
  raw_file="proxy_scan_raw_${host}_${ts}.txt"
  declare -A grouped
  grouped=( ["200 OK"]=() ["403 Forbidden"]=() ["429 Too Many Requests"]=() ["502 Bad Gateway"]=() ["Others"]=() )
  declare -A counters
  counters=( ["200 OK"]=0 ["403 Forbidden"]=0 ["429 Too Many Requests"]=0 ["502 Bad Gateway"]=0 ["Others"]=0 )
  for p in "${ALL_PROXIES[@]}"; do
    while [ "$(jobs -rp | wc -l)" -ge "$MAX_JOBS" ]; do sleep 0.08; done
    {
      resp=$(send_connect "$p" 8080 "$host")
      status=$(categorize "$resp")
      printf "%s\n%s\n" "$status|$p" "$resp" > /tmp/fb_proxy_${host}_${RANDOM}_$$
    } &
  done
  wait
  results=()
  for f in /tmp/fb_proxy_${host}_*; do
    [ -f "$f" ] || continue
    headline=$(sed -n '1p' "$f")
    resp=$(sed -n '2,$p' "$f")
    status=${headline%%|*}
    proxyip=${headline#*|}
    counters["$status"]=$((counters["$status"]+1))
    grouped["$status"]+="$proxyip"$'\n'
    results+=( "$proxyip → $status"$'\n'"$resp"$'\n'"════════════════════════════════════════════════════════════════════════'" )
    printf "%b[%d/%d] Proxy: %s%b\n" "$CHOST" "${#results}" "${#ALL_PROXIES[@]}" "$proxyip" "$CRESET"
    printf "  %bStatus:%b %s\n" "$CSTATUS" "$CRESET" "$(color_for "$status")$status${CRESET}"
    print_summary counters
    printf "%b%s%b\n" "$C_OTHER" "$(printf '─%.0s' {1..60})" "$CRESET"
    rm -f "$f"
  done
  {
    echo "Scan target: $host"
    echo "Scanned at: $(date --iso-8601=seconds 2>/dev/null || date)"
    echo
    for key in "200 OK" "429 Too Many Requests" "502 Bad Gateway" "403 Forbidden" "Others"; do
      echo "$key (${counters[$key]}):"
      if [ -n "${grouped[$key]}" ]; then printf "  %s\n" "${grouped[$key]}" | sed 's/^/  /'; else echo "  (None)"; fi
      echo
    done
    echo
    echo "=== Raw responses below ==="
    echo
    for r in "${results[@]}"; do
      echo "$r"
      echo
    done
  } > "$grouped_file"
  printf "%bSaved grouped results to %s%b\n" "$C200" "$grouped_file" "$CRESET"
  printf "%s\n" "${results[@]}" > "$raw_file"
  printf "%bSaved raw results to %s%b\n" "$C200" "$raw_file" "$CRESET"
}
mode_multi_hosts_all_proxies(){
  echo -e "\n${CPROMPT}Enter hosts (one per line), 'done' to finish:${CRESET}"
  hosts=()
  while read -r line; do
    [ "$line" = "done" ] && break
    [ -z "$line" ] && continue
    hosts+=( "$line" )
  done
  if [ ${#hosts[@]} -eq 0 ]; then
    read -rp $'\n'"No manual hosts entered. Load from (f)ile, (u)rl or (s)kip? (f/u/s): " opt
    case "$opt" in
      f)
        read -rp "Enter path to .txt file: " fp
        mapfile -t hosts < <(sed -n '/\S/p' "$fp" 2>/dev/null)
        ;;
      u)
        read -rp "Enter URL (http/https raw): " url
        if command -v curl >/dev/null 2>&1; then
          mapfile -t hosts < <(curl -fsSL "$url")
        else
          echo "curl not found."
          return
        fi
        ;;
      *)
        echo -e "${C403}No hosts provided. Returning to main menu.${CRESET}"
        return
        ;;
    esac
  fi
  echo -e "\n${BOLD}Scanning ${#hosts[@]} hosts through ${#ALL_PROXIES[@]} proxies each (port 8080)...${CRESET}"
  ts=$(now_ts)
  grouped_file="multi_hosts_proxy_grouped_${ts}.txt"
  raw_file="multi_hosts_proxy_raw_${ts}.txt"
  {
    for host in "${hosts[@]}"; do
      echo "Host: $host" >> "$grouped_file"
      declare -A grouped
      grouped=( ["200 OK"]=() ["403 Forbidden"]=() ["429 Too Many Requests"]=() ["502 Bad Gateway"]=() ["Others"]=() )
      results=()
      for p in "${ALL_PROXIES[@]}"; do
        while [ "$(jobs -rp | wc -l)" -ge "$MAX_JOBS" ]; do sleep 0.08; done
        {
          resp=$(send_connect "$p" 8080 "$host")
          status=$(categorize "$resp")
          printf "%s\n%s\n" "$status|$p" "$resp" > /tmp/fb_multiproxy_${host}_${RANDOM}_$$
        } &
      done
      wait
      for f in /tmp/fb_multiproxy_${host}_*; do
        [ -f "$f" ] || continue
        head=$(sed -n '1p' "$f")
        resp=$(sed -n '2,$p' "$f")
        status=${head%%|*}; proxyip=${head#*|}
        grouped["$status"]+="$proxyip"$'\n'
        results+=( "$proxyip → $status"$'\n'"$resp"$'\n'"════════════════════════════════════════════════════════════════════════' )
        rm -f "$f"
      done
      for key in "200 OK" "429 Too Many Requests" "502 Bad Gateway" "403 Forbidden" "Others"; do
        echo "  $key (${#$(echo -n "${grouped[$key]}" | sed '/^$/d' | wc -l)}) :" >> "$grouped_file"
        if [ -n "${grouped[$key]}" ]; then
          printf "    %s\n" "${grouped[$key]}" >> "$grouped_file"
        else
          echo "    (None)" >> "$grouped_file"
        fi
        echo "" >> "$grouped_file"
      done
      echo "------------------------------------------------------------" >> "$grouped_file"
      echo "=== Host: $host ===" >> "$raw_file"
      for r in "${results[@]}"; do
        echo "$r" >> "$raw_file"
      done
      echo "" >> "$raw_file"
    done
  }
  echo -e "${C200}Saved grouped multi-host results to ${grouped_file}${CRESET}"
  echo -e "${C200}Saved raw multi-host results to ${raw_file}${CRESET}"
}
cleanup(){
  rm -f /tmp/fb_result_$$_* /tmp/fb_proxy_* /tmp/fb_multiproxy_* 2>/dev/null
}
trap cleanup EXIT
print_banner
while true; do
  echo -e "\n${CTITLE}${BOLD}MAIN MENU:${CRESET}"
  echo -e "  ${CMENU}1.${CRESET} Single Host Check (use PROXY_IP/default single proxy)"
  echo -e "  ${CMENU}2.${CRESET} Multiple Host Check (manual input, uses PROXY_IP)"
  echo -e "  ${CMENU}3.${CRESET} Load hosts from file (uses PROXY_IP)"
  echo -e "  ${CMENU}4.${CRESET} Load hosts from URL (uses PROXY_IP)"
  echo -e "  ${CMENU}5.${CRESET} Scan single host through ALL proxies (port 8080, grouped file)"
  echo -e "  ${CMENU}6.${CRESET} Scan multiple hosts through ALL proxies (port 8080, grouped file)"
  echo -e "  ${CMENU}7.${CRESET} Exit"
  echo -e "${CTITLE}------------------------------------------------------------${CRESET}"
  read -rp $'\n'"Select (1-7): " choice
  case "$choice" in
    1) mode_single_host ;;
    2) mode_multiple_hosts ;;
    3)
      read -rp "Enter path to .txt file: " fpath
      if [ -f "$fpath" ]; then
        mapfile -t hosts < <(sed -n '/\S/p' "$fpath")
        if [ ${#hosts[@]} -gt 0 ]; then
          printf "%s\n" "${hosts[@]}" > /tmp/fb_manual_hosts_$$
          echo -e "\n${BOLD}Scanning ${#hosts[@]} hosts via ${PROXY_IP}:${PROXY_PORT}...${CRESET}"
          temp_hosts=("${hosts[@]}")
          for h in "${temp_hosts[@]}"; do
            while [ "$(jobs -rp | wc -l)" -ge "$MAX_JOBS" ]; do sleep 0.08; done
            {
              resp=$(send_connect "$PROXY_IP" "$PROXY_PORT" "$h")
              status=$(categorize "$resp")
              printf "%s\n%s\n" "$status|$h" "$resp" > /tmp/fb_result_$$_"$RANDOM"
            } &
          done
          wait
          declare -A summary
          summary=( ["200 OK"]=0 ["403 Forbidden"]=0 ["429 Too Many Requests"]=0 ["502 Bad Gateway"]=0 ["Others"]=0 )
          results=(); hosts_200=(); hosts_403=(); hosts_429=(); hosts_502=(); hosts_others=()
          for f in /tmp/fb_result_$$_*; do
            [ -f "$f" ] || continue
            IFS='|' read -r status host < <(sed -n '1p' "$f")
            rest=$(sed -n '2,$p' "$f")
            summary["$status"]=$((summary["$status"] + 1))
            case "$status" in
              "200 OK") hosts_200+=( "$host" ) ;;
              "403 Forbidden") hosts_403+=( "$host" ) ;;
              "429 Too Many Requests") hosts_429+=( "$host" ) ;;
              "502 Bad Gateway") hosts_502+=( "$host" ) ;;
              *) hosts_others+=( "$host" ) ;;
            esac
            results+=( "$status → $host"$'\n'"$rest"$'\n'"════════════════════════════════════════════════════════════════════════' )
            rm -f "$f"
          done
          ts=$(now_ts)
          grouped_file="hosts_grouped_${ts}.txt"
          {
            echo "200 OK hosts"
            if [ ${#hosts_200[@]} -gt 0 ]; then for x in "${hosts_200[@]}"; do echo "$x"; done; else echo "(None)"; fi
            echo; echo "429 Too Many Requests hosts"
            if [ ${#hosts_429[@]} -gt 0 ]; then for x in "${hosts_429[@]}"; do echo "$x"; done; else echo "(None)"; fi
            echo; echo "502 Bad Gateway hosts"
            if [ ${#hosts_502[@]} -gt 0 ]; then for x in "${hosts_502[@]}"; do echo "$x"; done; else echo "(None)"; fi
            echo; echo "Others hosts"
            if [ ${#hosts_others[@]} -gt 0 ]; then for x in "${hosts_others[@]}"; do echo "$x"; done; else echo "(None)"; fi
            echo; echo "403 Forbidden hosts"
            if [ ${#hosts_403[@]} -gt 0 ]; then for x in "${hosts_403[@]}"; do echo "$x"; done; else echo "(None)"; fi
          } > "$grouped_file"
          echo -e "${C200}Saved grouped hosts to ${grouped_file}${CRESET}"
          raw_file="scan_results_${ts}.txt"
          printf "%s\n" "${results[@]}" > "$raw_file"
          echo -e "${C200}Saved raw results to ${raw_file}${CRESET}"
          rm -f /tmp/fb_manual_hosts_$$
        else
          echo "No hosts found in file."
        fi
      else
        echo "File not found."
      fi
      ;;
    4)
      read -rp "Enter URL (http/https raw link): " url
      if command -v curl >/dev/null 2>&1; then
        mapfile -t hosts < <(curl -fsSL "$url")
        if [ ${#hosts[@]} -eq 0 ]; then echo "No hosts fetched from URL."; else
          printf "%s\n" "${hosts[@]}" > /tmp/fb_manual_hosts_$$
          echo "Loaded ${#hosts[@]} hosts from URL."
          for h in "${hosts[@]}"; do
            while [ "$(jobs -rp | wc -l)" -ge "$MAX_JOBS" ]; do sleep 0.08; done
            {
              resp=$(send_connect "$PROXY_IP" "$PROXY_PORT" "$h")
              status=$(categorize "$resp")
              printf "%s\n%s\n" "$status|$h" "$resp" > /tmp/fb_result_$$_"$RANDOM"
            } &
          done
          wait
          declare -A summary
          summary=( ["200 OK"]=0 ["403 Forbidden"]=0 ["429 Too Many Requests"]=0 ["502 Bad Gateway"]=0 ["Others"]=0 )
          results=(); hosts_200=(); hosts_403=(); hosts_429=(); hosts_502=(); hosts_others=()
          for f in /tmp/fb_result_$$_*; do
            [ -f "$f" ] || continue
            IFS='|' read -r status host < <(sed -n '1p' "$f")
            rest=$(sed -n '2,$p' "$f")
            summary["$status"]=$((summary["$status"] + 1))
            case "$status" in
              "200 OK") hosts_200+=( "$host" ) ;;
              "403 Forbidden") hosts_403+=( "$host" ) ;;
              "429 Too Many Requests") hosts_429+=( "$host" ) ;;
              "502 Bad Gateway") hosts_502+=( "$host" ) ;;
              *) hosts_others+=( "$host" ) ;;
            esac
            results+=( "$status → $host"$'\n'"$rest"$'\n'"════════════════════════════════════════════════════════════════════════' )
            rm -f "$f"
          done
          ts=$(now_ts)
          grouped_file="hosts_grouped_${ts}.txt"
          {
            echo "200 OK hosts"
            if [ ${#hosts_200[@]} -gt 0 ]; then for x in "${hosts_200[@]}"; do echo "$x"; done; else echo "(None)"; fi
            echo; echo "429 Too Many Requests hosts"
            if [ ${#hosts_429[@]} -gt 0 ]; then for x in "${hosts_429[@]}"; do echo "$x"; done; else echo "(None)"; fi
            echo; echo "502 Bad Gateway hosts"
            if [ ${#hosts_502[@]} -gt 0 ]; then for x in "${hosts_502[@]}"; do echo "$x"; done; else echo "(None)"; fi
            echo; echo "Others hosts"
            if [ ${#hosts_others[@]} -gt 0 ]; then for x in "${hosts_others[@]}"; do echo "$x"; done; else echo "(None)"; fi
       
