// 슬라이드 p13-v12-pc-attr — 특성은 어디에 붙나, C# 12.0
using System;
using System.Linq;
using System.Reflection;

[AttributeUsage(AttributeTargets.All)]
class TagAttribute(string name) : Attribute
{
    public string Name => name;
}

[Tag("type")]
[method: Tag("ctor")]
class Point([Tag("param")] int x)
{
    public int X => x;
}

class App
{
    static string Tags(ICustomAttributeProvider p)
    {
        var s = string.Join(",", p.GetCustomAttributes(false)
            .OfType<TagAttribute>().Select(a => a.Name));
        return s.Length > 0 ? s : "(none)";
    }

    static void Main()
    {
        var t = typeof(Point);
        var c = t.GetConstructors()[0];
        Console.WriteLine("type  " + Tags(t));
        Console.WriteLine("ctor  " + Tags(c));
        Console.WriteLine("param " + Tags(c.GetParameters()[0]));
        var f = t.GetField("<x>P",
            BindingFlags.NonPublic | BindingFlags.Instance);
        Console.WriteLine("field " + Tags(f));
    }
}
