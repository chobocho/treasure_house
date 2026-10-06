// 슬라이드 p14-v13-pp-attr — 두 조각의 특성이 합쳐진다, C# 13.0
using System;
using System.Linq;
using System.Reflection;

[AttributeUsage(AttributeTargets.All, AllowMultiple = true)]
class TagAttribute : Attribute
{
    public string V;
    public TagAttribute(string v) { V = v; }
}

partial class C
{
    [Tag("def")] public partial int P { [Tag("def-get")] get; }
    public partial int this[[Tag("def-x")] int x] { get; }
}

partial class C
{
    [Tag("impl")] public partial int P { [Tag("impl-get")] get => 1; }
    public partial int this[[Tag("impl-x")] int x] => x;
}

class App
{
    static string Tags(ICustomAttributeProvider p) => string.Join(" ",
        p.GetCustomAttributes(typeof(TagAttribute), false)
         .Cast<TagAttribute>().Select(t => t.V).OrderBy(v => v));

    static void Main()
    {
        var p = typeof(C).GetProperty("P");
        Console.WriteLine("P:     " + Tags(p));
        Console.WriteLine("get:   " + Tags(p.GetMethod));
        var ix = typeof(C).GetProperty("Item");
        Console.WriteLine("x:     " + Tags(ix.GetIndexParameters()[0]));
        Console.WriteLine("props: " + typeof(C).GetProperties().Length);
    }
}
