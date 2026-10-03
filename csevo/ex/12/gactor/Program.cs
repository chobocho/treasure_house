// 슬라이드 p12-v11-genattr-ctor — 생성자 매개변수가 T 인 특성, C# 11.0
using System;
using System.Reflection;

class RangeAttribute<T> : Attribute
{
    public RangeAttribute(T min, T max) { Min = min; Max = max; }
    public T Min { get; }
    public T Max { get; }
    public T Default { get; set; }
}

class Settings
{
    [Range<int>(1, 64, Default = 8)] public int Threads = 8;
    [Range<double>(0.0, 1.0)] public double Ratio = 0.5;
#if DEC
    [Range<decimal>(0, 100)] public decimal Price = 1;
#endif
}

class App
{
    static void Main()
    {
        var t = typeof(Settings).GetField("Threads")
            .GetCustomAttribute<RangeAttribute<int>>();
        Console.WriteLine($"{t.Min}..{t.Max}, default {t.Default}");
        CustomAttributeData d = typeof(Settings).GetField("Ratio")
            .GetCustomAttributesData()[0];
        foreach (CustomAttributeTypedArgument a
                 in d.ConstructorArguments)
            Console.WriteLine($"{a.ArgumentType.Name} {a.Value}");
    }
}
