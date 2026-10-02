// 슬라이드 p10-v9-init-modreq — init 의 메타데이터, C# 9.0
using System;
using System.Reflection;

class Person
{
    public string Name { get; init; }
    public int Age { get; set; }
}

class App
{
    static void Show(PropertyInfo p)
    {
        MethodInfo set = p.SetMethod;
        Type[] mods = set.ReturnParameter.GetRequiredCustomModifiers();
        Console.WriteLine("{0,-4} {1} {2} modreq: {3}", p.Name,
            set.Name, set.IsPublic ? "public" : "?",
            mods.Length == 0 ? "-" : mods[0].FullName);
    }

    static void Main()
    {
        Show(typeof(Person).GetProperty("Name"));
        Show(typeof(Person).GetProperty("Age"));
        var p = new Person { Name = "ann" };
        typeof(Person).GetProperty("Name").SetValue(p, "bob");
        Console.WriteLine("after reflection: " + p.Name);
        dynamic d = p;
        try { d.Name = "cat"; }
        catch (Exception e) { Console.WriteLine(e.Message); }
        Console.WriteLine("after dynamic:    " + p.Name);
    }
}
