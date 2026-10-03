// 슬라이드 p11-v10-la-attr — 람다에 특성, C# 10.0
using System;
using System.Reflection;

[AttributeUsage(AttributeTargets.All, AllowMultiple = true)]
class TagAttribute : Attribute
{
    public string Text;
    public TagAttribute(string text) { Text = text; }
}

class App
{
    static string Tag(ICustomAttributeProvider p)
    {
        object[] a = p.GetCustomAttributes(typeof(TagAttribute), false);
        return a.Length == 1 ? ((TagAttribute)a[0]).Text : "-";
    }

    static void Main()
    {
        var get = [Tag("get")] () => 1;
        var echo = [return: Tag("ret")] ([Tag("p")] string s) => s;
        var two = [Tag("a"), Obsolete][Tag("b")] (int x) => x;

        MethodInfo m = echo.Method;
        Console.WriteLine($"get    method={Tag(get.Method)}");
        Console.WriteLine($"echo   return={Tag(m.ReturnParameter)}" +
                          $" param={Tag(m.GetParameters()[0])}");
        int n = two.Method.GetCustomAttributes(false).Length;
        Console.WriteLine($"two    {n} attributes");
        Console.WriteLine($"name   {m.Name}  on {m.DeclaringType}");
#if BAD
        Func<int, int> f1 = [Tag("x")] x => x;    // needs (x)
#endif
    }
}
