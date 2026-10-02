// 슬라이드 p10-v9-rec-members — 컴파일러가 만드는 멤버, C# 9.0
using System;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;

record P(int X);
sealed record S(int X);

class App
{
    const BindingFlags All = BindingFlags.Public
        | BindingFlags.NonPublic | BindingFlags.Instance
        | BindingFlags.Static | BindingFlags.DeclaredOnly;

    static string Key(MemberInfo m) => Regex.Replace(
        char.ToLower(m.MemberType.ToString()[0]) + " " + m,
        @"\b[PS]\b|System\.|Text\.",
        x => x.Value.Length == 1 ? "R" : "");

    static string Kind(Type t, string key)
    {
        MemberInfo m = t.GetMembers(All)
            .FirstOrDefault(x => Key(x) == key);
        MethodBase b = m as MethodBase
            ?? (m as PropertyInfo)?.GetMethod;
        if (b == null) return m == null ? "-" : "field";
        string acc = b.IsPublic ? "public" : b.IsPrivate ? "private"
            : b.IsFamily ? "protected" : "other";
        string v = b.IsAbstract ? " abstract"
            : b.IsVirtual && !b.IsFinal ? " virtual" : "";
        return acc + (b.IsStatic ? " static" : "") + v;
    }

    static void Main()
    {
        foreach (string k in typeof(P).GetMembers(All).Select(Key)
                     .OrderBy(s => s, StringComparer.Ordinal))
            Console.WriteLine("{0,-37}|{1,-18}|{2}", k,
                Kind(typeof(P), k), Kind(typeof(S), k));
    }
}
