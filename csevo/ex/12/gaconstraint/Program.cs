// 슬라이드 p12-v11-genattr-why — 형식 매개변수 제약이 특성에, C# 11.0
using System;
using System.Reflection;

class ParseWithAttribute : Attribute          // old style
{
    public ParseWithAttribute(Type t) => Target = t;
    public Type Target { get; }
}

class ParseAsAttribute<T> : Attribute where T : IParsable<T>
{
    public object Parse(string s) => T.Parse(s, null);
}

class Form
{
    [ParseWith(typeof(object))] public string Age = "42";   // accepted
    [ParseAs<int>] public string Height = "180";
#if BAD
    [ParseAs<object>] public string Name = "Ada";
#endif
}

class App
{
    static void Main()
    {
        FieldInfo age = typeof(Form).GetField("Age");
        Type t = age.GetCustomAttribute<ParseWithAttribute>().Target;
        MethodInfo parse = t.GetMethod("Parse",
            new[] { typeof(string) });
        Console.WriteLine("old style found Parse: " + (parse != null));

        FieldInfo h = typeof(Form).GetField("Height");
        var p = h.GetCustomAttribute<ParseAsAttribute<int>>();
        object v = p.Parse((string)h.GetValue(new Form()));
        Console.WriteLine($"new style: {v} ({v.GetType().Name})");
    }
}
