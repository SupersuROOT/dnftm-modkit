using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace DNFTMModLoader
{
    /// <summary>
    /// Raw JSON number: keeps the original text so values round-trip exactly.
    /// </summary>
    internal sealed class JsonNumber
    {
        public readonly string Text;
        public JsonNumber(string text) { Text = text; }
        public override string ToString() { return Text; }
    }

    /// <summary>
    /// Small, dependency-free JSON reader/writer. Objects keep key order (game files rely on
    /// readable order only, but it makes diffs of merged output easy to inspect).
    /// Objects are List of KeyValuePair wrapped in JsonObject; arrays are List&lt;object&gt;.
    /// </summary>
    internal sealed class JsonObject
    {
        public readonly List<string> Keys = new List<string>();
        public readonly Dictionary<string, object> Values = new Dictionary<string, object>();

        public bool Has(string key) { return Values.ContainsKey(key); }

        public object this[string key]
        {
            get { object v; return Values.TryGetValue(key, out v) ? v : null; }
            set
            {
                if (!Values.ContainsKey(key)) Keys.Add(key);
                Values[key] = value;
            }
        }
    }

    internal static class MiniJson
    {
        public static object Parse(string text)
        {
            var p = new Parser(text);
            p.SkipWs();
            object v = p.ReadValue();
            p.SkipWs();
            if (!p.AtEnd) throw p.Error("Unexpected trailing characters");
            return v;
        }

        public static string Serialize(object value)
        {
            var sb = new StringBuilder();
            Write(sb, value, 0);
            return sb.ToString();
        }

        /// <summary>
        /// Deep-merge <paramref name="patch"/> into <paramref name="target"/>:
        /// objects merge key by key, anything else (arrays, scalars) replaces.
        /// A key whose value is null removes the key.
        /// </summary>
        public static object Merge(object target, object patch)
        {
            var t = target as JsonObject;
            var p = patch as JsonObject;
            if (t == null || p == null) return patch;
            foreach (string k in p.Keys)
            {
                object pv = p.Values[k];
                if (pv == null)
                {
                    if (t.Values.Remove(k)) t.Keys.Remove(k);
                    continue;
                }
                t[k] = t.Has(k) ? Merge(t[k], pv) : pv;
            }
            return t;
        }

        static void Write(StringBuilder sb, object v, int depth)
        {
            if (v == null) { sb.Append("null"); return; }
            var s = v as string;
            if (s != null) { WriteString(sb, s); return; }
            if (v is bool) { sb.Append((bool)v ? "true" : "false"); return; }
            var n = v as JsonNumber;
            if (n != null) { sb.Append(n.Text); return; }
            if (v is int || v is long || v is double || v is float)
            {
                sb.Append(Convert.ToString(v, CultureInfo.InvariantCulture));
                return;
            }
            var o = v as JsonObject;
            if (o != null)
            {
                sb.Append('{');
                bool first = true;
                foreach (string k in o.Keys)
                {
                    if (!first) sb.Append(',');
                    first = false;
                    WriteString(sb, k);
                    sb.Append(':');
                    Write(sb, o.Values[k], depth + 1);
                }
                sb.Append('}');
                return;
            }
            var a = v as List<object>;
            if (a != null)
            {
                sb.Append('[');
                for (int i = 0; i < a.Count; i++)
                {
                    if (i > 0) sb.Append(',');
                    Write(sb, a[i], depth + 1);
                }
                sb.Append(']');
                return;
            }
            WriteString(sb, v.ToString());
        }

        static void WriteString(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    case '\b': sb.Append("\\b"); break;
                    case '\f': sb.Append("\\f"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c); // game parser reads raw UTF-8 text fine
                        break;
                }
            }
            sb.Append('"');
        }

        sealed class Parser
        {
            readonly string s;
            int i;

            public Parser(string text)
            {
                s = text ?? string.Empty;
                if (s.Length > 0 && s[0] == '﻿') i = 1; // BOM
            }

            public bool AtEnd { get { return i >= s.Length; } }

            public Exception Error(string msg)
            {
                int line = 1;
                for (int k = 0; k < i && k < s.Length; k++) if (s[k] == '\n') line++;
                return new FormatException(msg + " (line " + line + ")");
            }

            public void SkipWs()
            {
                while (i < s.Length)
                {
                    char c = s[i];
                    if (c == ' ' || c == '\t' || c == '\r' || c == '\n') { i++; continue; }
                    // Allow // and /* */ comments in mod files; they are stripped on output.
                    if (c == '/' && i + 1 < s.Length && s[i + 1] == '/')
                    {
                        while (i < s.Length && s[i] != '\n') i++;
                        continue;
                    }
                    if (c == '/' && i + 1 < s.Length && s[i + 1] == '*')
                    {
                        int end = s.IndexOf("*/", i + 2, StringComparison.Ordinal);
                        i = end < 0 ? s.Length : end + 2;
                        continue;
                    }
                    break;
                }
            }

            public object ReadValue()
            {
                if (AtEnd) throw Error("Unexpected end of input");
                char c = s[i];
                if (c == '{') return ReadObject();
                if (c == '[') return ReadArray();
                if (c == '"') return ReadString();
                if (c == '-' || (c >= '0' && c <= '9')) return ReadNumber();
                if (Match("true")) return true;
                if (Match("false")) return false;
                if (Match("null")) return null;
                throw Error("Unexpected character '" + c + "'");
            }

            bool Match(string word)
            {
                if (string.CompareOrdinal(s, i, word, 0, word.Length) == 0)
                {
                    i += word.Length;
                    return true;
                }
                return false;
            }

            JsonObject ReadObject()
            {
                var o = new JsonObject();
                i++; // {
                SkipWs();
                if (!AtEnd && s[i] == '}') { i++; return o; }
                while (true)
                {
                    SkipWs();
                    if (AtEnd || s[i] != '"') throw Error("Expected property name");
                    string key = ReadString();
                    SkipWs();
                    if (AtEnd || s[i] != ':') throw Error("Expected ':'");
                    i++;
                    SkipWs();
                    o[key] = ReadValue();
                    SkipWs();
                    if (AtEnd) throw Error("Unterminated object");
                    if (s[i] == ',')
                    {
                        i++;
                        SkipWs();
                        if (!AtEnd && s[i] == '}') { i++; return o; } // trailing comma
                        continue;
                    }
                    if (s[i] == '}') { i++; return o; }
                    throw Error("Expected ',' or '}'");
                }
            }

            List<object> ReadArray()
            {
                var a = new List<object>();
                i++; // [
                SkipWs();
                if (!AtEnd && s[i] == ']') { i++; return a; }
                while (true)
                {
                    SkipWs();
                    a.Add(ReadValue());
                    SkipWs();
                    if (AtEnd) throw Error("Unterminated array");
                    if (s[i] == ',')
                    {
                        i++;
                        SkipWs();
                        if (!AtEnd && s[i] == ']') { i++; return a; } // trailing comma
                        continue;
                    }
                    if (s[i] == ']') { i++; return a; }
                    throw Error("Expected ',' or ']'");
                }
            }

            string ReadString()
            {
                var sb = new StringBuilder();
                i++; // opening quote
                while (true)
                {
                    if (AtEnd) throw Error("Unterminated string");
                    char c = s[i++];
                    if (c == '"') return sb.ToString();
                    if (c != '\\') { sb.Append(c); continue; }
                    if (AtEnd) throw Error("Bad escape");
                    char e = s[i++];
                    switch (e)
                    {
                        case '"': sb.Append('"'); break;
                        case '\\': sb.Append('\\'); break;
                        case '/': sb.Append('/'); break;
                        case 'b': sb.Append('\b'); break;
                        case 'f': sb.Append('\f'); break;
                        case 'n': sb.Append('\n'); break;
                        case 'r': sb.Append('\r'); break;
                        case 't': sb.Append('\t'); break;
                        case 'u':
                            if (i + 4 > s.Length) throw Error("Bad \\u escape");
                            sb.Append((char)int.Parse(s.Substring(i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                            i += 4;
                            break;
                        default: throw Error("Bad escape \\" + e);
                    }
                }
            }

            JsonNumber ReadNumber()
            {
                int start = i;
                if (s[i] == '-') i++;
                while (i < s.Length && "0123456789.eE+-".IndexOf(s[i]) >= 0) i++;
                return new JsonNumber(s.Substring(start, i - start));
            }
        }
    }
}
