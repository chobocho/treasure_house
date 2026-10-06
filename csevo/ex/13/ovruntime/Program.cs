// 슬라이드 p13-v12-runtime — C# 12 기능이 기대는 형식, C# 12.0
using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

class App
{
    static void Show(Type t)
    {
        var u = (AttributeUsageAttribute)Attribute.GetCustomAttribute(
            t, typeof(AttributeUsageAttribute));
        string on = u.ValidOn.ToString();
        int n = on.Split(',').Length;
        Console.WriteLine($"{t.Name,-30} {t.Assembly.GetName().Name}");
        Console.WriteLine(n > 3 ? $"  on: {n} targets" : $"  on: {on}");
    }

    static void Main()
    {
        Show(typeof(InlineArrayAttribute));        // 7장
        Show(typeof(CollectionBuilderAttribute));  // 4장
        Show(typeof(ExperimentalAttribute));       // 8장
        Show(typeof(RequiresLocationAttribute));   // 6장
        var ic = "System.Runtime.CompilerServices."
               + "InterceptsLocationAttribute";
        Console.WriteLine($"{ic.Substring(32)}: "
            + (Type.GetType(ic) == null ? "none" : "found"));
    }
}
