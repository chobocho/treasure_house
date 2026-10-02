// 슬라이드 p8-v7_2-refstruct-meta — ref struct 의 메타데이터, C# 7.2
using System;
using System.Runtime.CompilerServices;

ref struct Mine
{
    public Span<byte> Data;
    public Mine(Span<byte> d) { Data = d; }
}

class App
{
    static void Show(Type t)
    {
        Console.WriteLine(t.Name + ": IsByRefLike=" + t.IsByRefLike);
        foreach (var a in t.GetCustomAttributes(false))
        {
            string text = a.GetType().Name;
            var o = a as ObsoleteAttribute;
            if (o != null) text += "\n    \"" + o.Message + "\"";
            var c = a as CompilerFeatureRequiredAttribute;
            if (c != null) text += " \"" + c.FeatureName + "\"";
            if (text.StartsWith("Is") || o != null || c != null)
                Console.WriteLine("  [" + text + "]");
        }
    }

    static void Main()
    {
        Show(typeof(Mine));
        Show(typeof(Span<>));
    }
}
