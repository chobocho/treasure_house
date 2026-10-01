// 슬라이드 p4-v3-var-need — 익명 형식은 var 로만, C# 3.0
using System;
using System.Reflection;

class App
{
    static void Main()
    {
        var p = new { Name = "Ann", Age = 31 };
        Console.WriteLine(p.Name + " " + (p.Age + 1)); // typed members

        object o = p;         // allowed, but object has no member Name;
        // what is left is reflection, with the name in a string
        PropertyInfo name = o.GetType().GetProperty("Name");
        Console.WriteLine(name.GetValue(o, null));
        PropertyInfo typo = o.GetType().GetProperty("Nmae");
        Console.WriteLine(typo == null ? "Nmae: not found" : "found");
    }
}
