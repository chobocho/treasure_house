// 슬라이드 p13-v12-pc-vs — 네 가지 형식의 같은 매개변수 목록, C# 12.0
using System;
using System.Reflection;

class C(int x) { public int Get() => x; }
struct S(int x) { public int Get() => x; }
record class RC(int X);
record struct RS(int X);

class App
{
    static readonly Type Ref = typeof(int).MakeByRefType();

    static string Has(Type t, string name, params Type[] ps) =>
        t.GetMethod(name, BindingFlags.Public | BindingFlags.Instance
            | BindingFlags.DeclaredOnly, ps) != null ? "yes" : "-";

    static void Row(Type t)
    {
        var all = BindingFlags.Public | BindingFlags.NonPublic
                | BindingFlags.Instance;
        string prop = t.GetProperty("X") != null ? "yes" : "-";
        string field = t.GetFields(all)[0].Name;
        string noArg = t.IsValueType
            || t.GetConstructor(Type.EmptyTypes) != null ? "yes" : "-";
        Console.WriteLine($"{t.Name,-3}|{prop,-5}|{field,-18}|"
            + $"{Has(t, "Equals", typeof(object)),-7}|"
            + $"{Has(t, "ToString"),-9}|"
            + $"{Has(t, "Deconstruct", Ref),-6}|"
            + noArg);
    }

    static void Main()
    {
        Console.WriteLine("   |prop |field             |Equals |"
            + "ToString |Decon |new()");
        foreach (var t in new[] { typeof(C), typeof(S),
                                  typeof(RC), typeof(RS) })
            Row(t);
    }
}
