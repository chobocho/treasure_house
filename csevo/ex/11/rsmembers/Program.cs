// 슬라이드 p11-v10-rs-members — 두 레코드의 멤버, C# 10.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;

record struct RS(int X);
record class RC(int X);

class App
{
    const BindingFlags All = BindingFlags.Public
        | BindingFlags.NonPublic | BindingFlags.Instance
        | BindingFlags.Static | BindingFlags.DeclaredOnly;

    static string Mark(MemberInfo m) =>
        (m is MethodBase mb && !mb.IsPublic ? "-" : "")
        + (m.IsDefined(typeof(IsReadOnlyAttribute)) ? "ro " : "")
        + (m is MethodInfo mi && mi.IsVirtual ? "virt " : "");

    static void Dump(Type t)
    {
        Console.WriteLine(t.Name + " : " + string.Join(", ",
            t.GetInterfaces().Select(i => i.Name)));
        foreach (var m in t.GetMembers(All)
                     .Where(m => m.MemberType != MemberTypes.Field)
                     .OrderBy(m => m.Name).ThenBy(m => m.ToString()))
            Console.WriteLine("  " + Mark(m) + Regex.Replace(
                m.ToString().Replace("System.", ""),
                @"\b" + t.Name + @"\b", "R"));
    }

    static void Main()
    {
        Dump(typeof(RS));
        Dump(typeof(RC));
    }
}
