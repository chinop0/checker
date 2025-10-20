package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"io/ioutil"
	"net"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"sync"
	"time"
)

// ====== CONFIGURATION ======
const (
	PROXY_IP       = "157.240.195.32"
	PROXY_PORT     = 8080
	MAX_WORKERS    = 300
	SOCKET_TIMEOUT = 30 * time.Second
	RECV_BUFFER    = 8192
)

// ====== COLORS ======
const (
	COLOR_200    = "\033[38;5;40m"
	COLOR_403    = "\033[38;5;203m"
	COLOR_429    = "\033[38;5;214m"
	COLOR_502    = "\033[38;5;141m"
	COLOR_OTHER  = "\033[38;5;245m"
	COLOR_TITLE  = "\033[38;5;39m"
	COLOR_MENU   = "\033[38;5;45m"
	COLOR_PROMPT = "\033[38;5;51m"
	COLOR_STATUS = "\033[38;5;228m"
	COLOR_HOST   = "\033[38;5;117m"
	COLOR_RESET  = "\033[0m"
	BOLD         = "\033[1m"
)

// ====== FULL PROXY LIST (from your original Python) ======
var ALL_PROXIES = []string{
	"31.13.94.39","31.13.84.39","157.240.8.39","179.60.195.39","157.240.9.39",
	"157.240.234.38","157.240.222.32","31.13.85.39","157.240.226.38","157.240.12.39",
	"31.13.90.36","31.13.80.39","157.240.17.32","157.240.204.32","163.70.152.41",
	"57.144.114.4","157.240.30.39","185.60.217.39","157.240.27.39","57.144.248.4",
	"57.144.244.4","157.240.0.38","157.240.253.39","157.240.210.32","157.240.223.32",
	"157.240.200.32","102.132.97.39","102.132.103.36","157.240.243.39","31.13.83.39",
	"157.240.5.32","157.240.205.37","157.240.195.32","157.240.196.32","185.60.219.38",
	"157.240.202.37","163.70.128.38","57.144.238.4","57.144.240.4","163.70.151.38",
	"157.240.214.38","157.240.225.38","157.240.233.38","157.240.199.32","157.240.211.38",
	"57.144.100.4","157.240.208.32","31.13.95.38","31.13.73.38","157.240.23.37",
	"157.240.192.32","163.70.146.39","163.70.140.41","157.240.1.38","31.13.64.39",
	"157.240.16.38","157.240.242.39","163.70.144.33","157.240.237.39","57.144.124.4",
	"157.240.198.32","157.240.239.38","31.13.86.39","31.13.69.38","157.240.231.38",
	"157.240.209.32","31.13.82.39","31.13.76.32","157.240.215.32","157.240.244.39",
	"31.13.89.37","157.240.25.38","157.240.236.36","163.70.132.41","163.70.137.39",
	"102.132.101.38","57.144.222.4","157.240.201.32","31.13.78.37","157.240.227.38",
	"157.240.197.32","163.70.130.39","57.144.110.4","157.240.212.32","157.240.29.36",
	"185.60.218.39","31.13.72.39","57.144.152.4","57.144.14.4","57.144.160.4",
	"157.240.13.39","157.240.15.38","163.70.148.33","163.70.149.42","57.144.126.4",
	"31.13.87.39","157.240.224.39","31.13.66.32","157.240.229.38","57.144.22.4",
	"157.240.14.38","57.144.204.4","157.240.254.39","57.144.218.4","31.13.93.37",
	"57.144.104.4","157.240.24.37","57.144.252.4","31.13.88.38","31.13.70.39",
	"157.240.11.39","157.240.26.39","57.144.116.4","57.144.102.4","157.240.22.38",
	"157.240.3.39","31.13.71.39","157.240.241.38","157.240.245.39","102.132.99.38",
	"102.132.104.41",
}

// ====== UTILITIES ======
func clearTerminal() {
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("cmd", "/c", "cls")
	} else {
		cmd = exec.Command("clear")
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	_ = cmd.Run()
}

func printBanner() {
	clearTerminal()
	width := 54
	title := "FreeBasics Checker"
	developer := "Developed by: FirewallFalcon"
	fmt.Printf("%s%s\n", COLOR_TITLE, BOLD)
	fmt.Printf("+%s+\n", strings.Repeat("-", width))
	fmt.Printf("|%s|\n", centerText(title, width))
	fmt.Printf("|%s|\n", centerText(developer, width))
	fmt.Printf("+%s+\n", strings.Repeat("-", width))
	fmt.Printf("%s\n", COLOR_RESET)
}

func centerText(s string, width int) string {
	if len(s) >= width {
		return s
	}
	pad := (width - len(s)) / 2
	return fmt.Sprintf("%s%s%s", strings.Repeat(" ", pad), s, strings.Repeat(" ", width-len(s)-pad))
}

func sendCustomPayload(proxyIP string, proxyPort int, targetHost string, targetPort int) string {
	payload := fmt.Sprintf("CONNECT %s:%d HTTP/1.1\r\n"+
		"Host: %s:%d\r\n"+
		"Proxy-Connection: keep-alive\r\n"+
		"User-Agent: Mozilla/5.0 (Linux; Android 14; SM-A245F) "+
		"Chrome/133.0.6943.122 [FBAN/InternetOrgApp;FBAV/166.0.0.0.169;]\r\n"+
		"X-IORG-BSID: a08359b0-d7ec-4cb5-97bf-000bdc29ec87\r\n"+
		"X-IORG-SERVICE-ID: null\r\n\r\n", targetHost, targetPort, targetHost, targetPort)

	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", proxyIP, proxyPort), SOCKET_TIMEOUT)
	if err != nil {
		return fmt.Sprintf("[ERROR] %s", err.Error())
	}
	defer conn.Close()
	conn.SetDeadline(time.Now().Add(SOCKET_TIMEOUT))

	_, err = conn.Write([]byte(payload))
	if err != nil {
		return fmt.Sprintf("[ERROR] %s", err.Error())
	}

	buf := make([]byte, RECV_BUFFER)
	n, err := conn.Read(buf)
	if err != nil && err != io.EOF {
		return fmt.Sprintf("[ERROR] %s", err.Error())
	}
	return string(buf[:n])
}

func categorizeResponse(resp string) string {
	if strings.HasPrefix(resp, "[ERROR]") {
		return "Others"
	}
	switch {
	case strings.Contains(resp, "200"):
		return "200 OK"
	case strings.Contains(resp, "403"):
		return "403 Forbidden"
	case strings.Contains(resp, "429"):
		return "429 Too Many Requests"
	case strings.Contains(resp, "502"):
		return "502 Bad Gateway"
	default:
		return "Others"
	}
}

func getColor(status string) string {
	switch status {
	case "200 OK":
		return COLOR_200
	case "403 Forbidden":
		return COLOR_403
	case "429 Too Many Requests":
		return COLOR_429
	case "502 Bad Gateway":
		return COLOR_502
	default:
		return COLOR_OTHER
	}
}

func printSummary(summary map[string]int) {
	maxLen := 0
	for k := range summary {
		if len(k) > maxLen {
			maxLen = len(k)
		}
	}
	fmt.Printf("\n%s%sSUMMARY:%s\n", COLOR_STATUS, BOLD, COLOR_RESET)
	for status, count := range summary {
		fmt.Printf("  %s%-*s%s : %d\n", getColor(status), maxLen, status, COLOR_RESET, count)
	}
}

// ====== FILE LOADERS ======
func loadHostsFromFile(filePath string) []string {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		fmt.Printf("%sFile not found: %s%s\n", COLOR_403, filePath, COLOR_RESET)
		return nil
	}
	lines := strings.Split(string(data), "\n")
	out := []string{}
	for _, l := range lines {
		s := strings.TrimSpace(l)
		if s != "" {
			out = append(out, s)
		}
	}
	return out
}

func loadHostsFromURL(url string) []string {
	client := http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		fmt.Printf("%sError fetching URL: %s%s\n", COLOR_403, err, COLOR_RESET)
		return nil
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		fmt.Printf("%sFailed to fetch URL (status %d)%s\n", COLOR_403, resp.StatusCode, COLOR_RESET)
		return nil
	}
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("%sError reading URL body: %s%s\n", COLOR_403, err, COLOR_RESET)
		return nil
	}
	lines := strings.Split(string(b), "\n")
	out := []string{}
	for _, l := range lines {
		s := strings.TrimSpace(l)
		if s != "" {
			out = append(out, s)
		}
	}
	return out
}

// ====== SCAN: multiple hosts via single proxy (like Python option 2/3/4) ======
func scanMultipleHosts(proxyIP string, proxyPort int, hosts []string) {
	results := []string{}
	summary := map[string]int{"200 OK": 0, "403 Forbidden": 0, "429 Too Many Requests": 0, "502 Bad Gateway": 0, "Others": 0}
	hosts200, hosts403, hosts429, hosts502, hostsOthers := []string{}, []string{}, []string{}, []string{}, []string{}

	fmt.Printf("\n%sScanning %d hosts...%s\n\n", BOLD, len(hosts), COLOR_RESET)

	var wg sync.WaitGroup
	sem := make(chan struct{}, MAX_WORKERS)
	outCh := make(chan struct {
		host     string
		response string
	}, len(hosts))

	for _, h := range hosts {
		wg.Add(1)
		sem <- struct{}{}
		go func(host string) {
			defer wg.Done()
			defer func() { <-sem }()
			resp := sendCustomPayload(proxyIP, proxyPort, host, 443)
			outCh <- struct {
				host     string
				response string
			}{host: host, response: resp}
		}(h)
	}

	go func() {
		wg.Wait()
		close(outCh)
	}()

	i := 0
	for item := range outCh {
		i++
		status := categorizeResponse(item.response)
		summary[status]++
		switch status {
		case "200 OK":
			hosts200 = append(hosts200, item.host)
		case "403 Forbidden":
			hosts403 = append(hosts403, item.host)
		case "429 Too Many Requests":
			hosts429 = append(hosts429, item.host)
		case "502 Bad Gateway":
			hosts502 = append(hosts502, item.host)
		default:
			hostsOthers = append(hostsOthers, item.host)
		}

		fmt.Printf("%s[%d/%d] Checking: %s%s\n", COLOR_HOST, i, len(hosts), item.host, COLOR_RESET)
		fmt.Printf("  %sStatus:%s %s%s%s\n", COLOR_STATUS, COLOR_RESET, getColor(status), status, COLOR_RESET)
		printSummary(summary)
		fmt.Printf("%s%s%s\n", COLOR_OTHER, strings.Repeat("─", 60), COLOR_RESET)

		results = append(results, fmt.Sprintf("%s → %s\n%s\n%s", status, item.host, item.response, strings.Repeat("═", 50)))
	}

	// groups ordered like Python
	groupsOrdered := []struct {
		name  string
		hosts []string
	}{
		{"200 OK hosts", hosts200},
		{"429 Too Many Requests hosts", hosts429},
		{"502 Bad Gateway hosts", hosts502},
		{"Others hosts", hostsOthers},
		{"403 Forbidden hosts", hosts403},
	}

	timestamp := time.Now().Format("20060102_150405")
	groupedFilename := fmt.Sprintf("hosts_grouped_%s.txt", timestamp)
	f, err := os.Create(groupedFilename)
	if err == nil {
		defer f.Close()
		for _, g := range groupsOrdered {
			f.WriteString(g.name + "\n")
			if len(g.hosts) > 0 {
				for _, h := range g.hosts {
					f.WriteString(h + "\n")
				}
			} else {
				f.WriteString("(None)\n")
			}
			f.WriteString("\n")
		}
		fmt.Printf("%sSaved grouped hosts to %s%s\n", COLOR_200, groupedFilename, COLOR_RESET)
	} else {
		fmt.Printf("%sFailed to write grouped file: %v%s\n", COLOR_403, err, COLOR_RESET)
	}

	rawFilename := fmt.Sprintf("scan_results_%s.txt", timestamp)
	_ = ioutil.WriteFile(rawFilename, []byte(strings.Join(results, "\n")), 0644)
}

// ====== SCAN: single host through ALL_PROXIES (option 5) ======
func scanHostAgainstAllProxies(host string) {
	results := []string{}
	grouped := map[string][]string{"200 OK": {}, "403 Forbidden": {}, "429 Too Many Requests": {}, "502 Bad Gateway": {}, "Others": {}}
	summary := map[string]int{"200 OK": 0, "403 Forbidden": 0, "429 Too Many Requests": 0, "502 Bad Gateway": 0, "Others": 0}

	fmt.Printf("\n%sScanning host '%s' through %d proxies (port 8080)...%s\n\n", BOLD, host, len(ALL_PROXIES), COLOR_RESET)

	var wg sync.WaitGroup
	sem := make(chan struct{}, min(MAX_WORKERS, len(ALL_PROXIES)))
	outCh := make(chan struct {
		proxy    string
		response string
	}, len(ALL_PROXIES))

	for _, p := range ALL_PROXIES {
		wg.Add(1)
		sem <- struct{}{}
		go func(proxyIP string) {
			defer wg.Done()
			defer func() { <-sem }()
			resp := sendCustomPayload(proxyIP, 8080, host, 443)
			outCh <- struct {
				proxy    string
				response string
			}{proxy: proxyIP, response: resp}
		}(p)
	}

	go func() {
		wg.Wait()
		close(outCh)
	}()

	i := 0
	for item := range outCh {
		i++
		status := categorizeResponse(item.response)
		summary[status]++
		grouped[status] = append(grouped[status], item.proxy)

		fmt.Printf("%s[%d/%d] Proxy: %s%s\n", COLOR_HOST, i, len(ALL_PROXIES), item.proxy, COLOR_RESET)
		fmt.Printf("  %sStatus:%s %s%s%s\n", COLOR_STATUS, COLOR_RESET, getColor(status), status, COLOR_RESET)
		printSummary(summary)
		fmt.Printf("%s%s%s\n", COLOR_OTHER, strings.Repeat("─", 60), COLOR_RESET)

		results = append(results, fmt.Sprintf("%s → %s\n%s\n%s", item.proxy, status, item.response, strings.Repeat("═", 50)))
	}

	timestamp := time.Now().Format("20060102_150405")
	groupedFilename := fmt.Sprintf("proxy_scan_grouped_%s_%s.txt", sanitizeFilename(host), timestamp)
	rawFilename := fmt.Sprintf("proxy_scan_raw_%s_%s.txt", sanitizeFilename(host), timestamp)

	var buf bytes.Buffer
	buf.WriteString(fmt.Sprintf("Scan target: %s\nScanned at: %s\n\n", host, time.Now().Format(time.RFC3339)))
	keys := []string{"200 OK", "429 Too Many Requests", "502 Bad Gateway", "403 Forbidden", "Others"}
	for _, k := range keys {
		list := grouped[k]
		buf.WriteString(fmt.Sprintf("%s (%d):\n", k, len(list)))
		if len(list) > 0 {
			for _, p := range list {
				buf.WriteString(fmt.Sprintf("  %s\n", p))
			}
		} else {
			buf.WriteString("  (None)\n")
		}
		buf.WriteString("\n")
	}
	buf.WriteString("\n=== Raw responses below ===\n\n")
	for _, r := range results {
		buf.WriteString(r + "\n")
	}

	if err := ioutil.WriteFile(groupedFilename, buf.Bytes(), 0644); err == nil {
		fmt.Printf("%sSaved grouped results to %s%s\n", COLOR_200, groupedFilename, COLOR_RESET)
	} else {
		fmt.Printf("%sFailed to save grouped results: %v%s\n", COLOR_403, err, COLOR_RESET)
	}
	if err := ioutil.WriteFile(rawFilename, []byte(strings.Join(results, "\n")), 0644); err == nil {
		fmt.Printf("%sSaved raw results to %s%s\n", COLOR_200, rawFilename, COLOR_RESET)
	} else {
		fmt.Printf("%sFailed to save raw results: %v%s\n", COLOR_403, err, COLOR_RESET)
	}
}

// ====== SCAN: multiple hosts, each scanned through ALL_PROXIES (option 6) ======
func scanMultipleHostsAgainstAllProxies(hosts []string) {
	allResultsRaw := []struct {
		host    string
		results []string
	}{}
	allGroupedSummary := map[string]map[string][]string{}

	fmt.Printf("\n%sScanning %d hosts through %d proxies each (port 8080)...%s\n\n", BOLD, len(hosts), len(ALL_PROXIES), COLOR_RESET)

	for idx, host := range hosts {
		fmt.Printf("%s%sHost [%d/%d]: %s%s\n", COLOR_TITLE, BOLD, idx+1, len(hosts), host, COLOR_RESET)

		results := []string{}
		grouped := map[string][]string{"200 OK": {}, "403 Forbidden": {}, "429 Too Many Requests": {}, "502 Bad Gateway": {}, "Others": {}}
		summary := map[string]int{"200 OK": 0, "403 Forbidden": 0, "429 Too Many Requests": 0, "502 Bad Gateway": 0, "Others": 0}

		var wg sync.WaitGroup
		sem := make(chan struct{}, min(MAX_WORKERS, len(ALL_PROXIES)))
		outCh := make(chan struct {
			proxy    string
			response string
		}, len(ALL_PROXIES))

		for _, p := range ALL_PROXIES {
			wg.Add(1)
			sem <- struct{}{}
			go func(proxyIP string) {
				defer wg.Done()
				defer func() { <-sem }()
				resp := sendCustomPayload(proxyIP, 8080, host, 443)
				outCh <- struct {
					proxy    string
					response string
				}{proxy: proxyIP, response: resp}
			}(p)
		}

		go func() {
			wg.Wait()
			close(outCh)
		}()

		i := 0
		for item := range outCh {
			i++
			status := categorizeResponse(item.response)
			summary[status]++
			grouped[status] = append(grouped[status], item.proxy)

			fmt.Printf("%s[%d/%d] Proxy: %s%s\n", COLOR_HOST, i, len(ALL_PROXIES), item.proxy, COLOR_RESET)
			fmt.Printf("  %sStatus:%s %s%s%s\n", COLOR_STATUS, COLOR_RESET, getColor(status), status, COLOR_RESET)
			printSummary(summary)
			fmt.Printf("%s%s%s\n", COLOR_OTHER, strings.Repeat("─", 60), COLOR_RESET)

			results = append(results, fmt.Sprintf("%s → %s\n%s\n%s", item.proxy, status, item.response, strings.Repeat("═", 50)))
		}

		allResultsRaw = append(allResultsRaw, struct {
			host    string
			results []string
		}{host: host, results: results})
		allGroupedSummary[host] = grouped
	}

	timestamp := time.Now().Format("20060102_150405")
	groupedFilename := fmt.Sprintf("multi_hosts_proxy_grouped_%s.txt", timestamp)
	rawFilename := fmt.Sprintf("multi_hosts_proxy_raw_%s.txt", timestamp)

	var buf bytes.Buffer
	buf.WriteString(fmt.Sprintf("Multi-host proxy scan grouped results\nScanned at: %s\n\n", time.Now().Format(time.RFC3339)))
	for host, grouped := range allGroupedSummary {
		buf.WriteString(fmt.Sprintf("Host: %s\n", host))
		keys := []string{"200 OK", "429 Too Many Requests", "502 Bad Gateway", "403 Forbidden", "Others"}
		for _, key := range keys {
			list := grouped[key]
			buf.WriteString(fmt.Sprintf("  %s (%d):\n", key, len(list)))
			if len(list) > 0 {
				for _, p := range list {
					buf.WriteString(fmt.Sprintf("    %s\n", p))
				}
			} else {
				buf.WriteString("    (None)\n")
			}
			buf.WriteString("\n")
		}
		buf.WriteString("\n" + strings.Repeat("-", 60) + "\n\n")
	}
	buf.WriteString("\n=== Raw responses by host below ===\n\n")
	for _, hr := range allResultsRaw {
		buf.WriteString(fmt.Sprintf("=== Host: %s ===\n", hr.host))
		for _, r := range hr.results {
			buf.WriteString(r + "\n")
		}
		buf.WriteString("\n\n")
	}
	if err := ioutil.WriteFile(groupedFilename, buf.Bytes(), 0644); err == nil {
		fmt.Printf("%sSaved grouped multi-host results to %s%s\n", COLOR_200, groupedFilename, COLOR_RESET)
	} else {
		fmt.Printf("%sFailed to save grouped file: %v%s\n", COLOR_403, err, COLOR_RESET)
	}

	var rawBuf bytes.Buffer
	for _, hr := range allResultsRaw {
		rawBuf.WriteString(fmt.Sprintf("=== Host: %s ===\n", hr.host))
		rawBuf.WriteString(strings.Join(hr.results, "\n"))
		rawBuf.WriteString("\n\n")
	}
	if err := ioutil.WriteFile(rawFilename, rawBuf.Bytes(), 0644); err == nil {
		fmt.Printf("%sSaved raw multi-host results to %s%s\n", COLOR_200, rawFilename, COLOR_RESET)
	} else {
		fmt.Printf("%sFailed to save raw file: %v%s\n", COLOR_403, err, COLOR_RESET)
	}
}

// ====== HELPERS ======
func sanitizeFilename(s string) string {
	return strings.Map(func(r rune) rune {
		if r == '/' || r == '\\' || r == ':' || r == '*' || r == '?' || r == '"' || r == '<' || r == '>' || r == '|' {
			return '_'
		}
		return r
	}, s)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ====== MAIN MENU ======
func main() {
	printBanner()
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Printf("\n%s%sMAIN MENU:%s\n", COLOR_TITLE, BOLD, COLOR_RESET)
		fmt.Printf("  %s1.%s Single Host Check (use PROXY_IP/default single proxy)\n", COLOR_MENU, COLOR_RESET)
		fmt.Printf("  %s2.%s Multiple Host Check (manual input, uses PROXY_IP)\n", COLOR_MENU, COLOR_RESET)
		fmt.Printf("  %s3.%s Load hosts from file (uses PROXY_IP)\n", COLOR_MENU, COLOR_RESET)
		fmt.Printf("  %s4.%s Load hosts from URL (uses PROXY_IP)\n", COLOR_MENU, COLOR_RESET)
		fmt.Printf("  %s5.%s Scan single host through ALL proxies (port 8080, grouped file)\n", COLOR_MENU, COLOR_RESET)
		fmt.Printf("  %s6.%s Scan multiple hosts through ALL proxies (port 8080, grouped file)\n", COLOR_MENU, COLOR_RESET)
		fmt.Printf("  %s7.%s Exit\n", COLOR_MENU, COLOR_RESET)
		fmt.Printf("%s%s%s\n", COLOR_TITLE, strings.Repeat("─", 60), COLOR_RESET)

		fmt.Printf("\n%sSelect (1-7): %s", COLOR_PROMPT, COLOR_RESET)
		choice, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(choice)

		switch choice {
		case "1":
			fmt.Printf("%sEnter host: %s", COLOR_PROMPT, COLOR_RESET)
			host, _ := reader.ReadString('\n')
			host = strings.TrimSpace(host)
			if host != "" {
				scanMultipleHosts(PROXY_IP, PROXY_PORT, []string{host})
			}
		case "2":
			fmt.Printf("\n%sEnter hosts (one per line), 'done' to finish:%s\n", COLOR_PROMPT, COLOR_RESET)
			hosts := []string{}
			for {
				line, _ := reader.ReadString('\n')
				line = strings.TrimSpace(line)
				if strings.ToLower(line) == "done" {
					break
				}
				if line != "" {
					hosts = append(hosts, line)
				}
			}
			if len(hosts) > 0 {
				scanMultipleHosts(PROXY_IP, PROXY_PORT, hosts)
			}
		case "3":
			fmt.Printf("%sEnter path to .txt file: %s", COLOR_PROMPT, COLOR_RESET)
			filePath, _ := reader.ReadString('\n')
			filePath = strings.TrimSpace(filePath)
			hosts := loadHostsFromFile(filePath)
			if len(hosts) > 0 {
				scanMultipleHosts(PROXY_IP, PROXY_PORT, hosts)
			}
		case "4":
			fmt.Printf("%sEnter URL (e.g. GitHub raw link): %s", COLOR_PROMPT, COLOR_RESET)
			url, _ := reader.ReadString('\n')
			url = strings.TrimSpace(url)
			hosts := loadHostsFromURL(url)
			if len(hosts) > 0 {
				scanMultipleHosts(PROXY_IP, PROXY_PORT, hosts)
			}
		case "5":
			fmt.Printf("%sEnter target host to test through all proxies: %s", COLOR_PROMPT, COLOR_RESET)
			host, _ := reader.ReadString('\n')
			host = strings.TrimSpace(host)
			if host != "" {
				scanHostAgainstAllProxies(host)
			}
		case "6":
			fmt.Printf("\n%sEnter hosts (one per line), 'done' to finish:%s\n", COLOR_PROMPT, COLOR_RESET)
			hosts := []string{}
			for {
				line, _ := reader.ReadString('\n')
				line = strings.TrimSpace(line)
				if strings.ToLower(line) == "done" {
					break
				}
				if line != "" {
					hosts = append(hosts, line)
				}
			}
			if len(hosts) == 0 {
				fmt.Printf
