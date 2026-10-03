// 슬라이드 p12-v11-rq-attr — 특성 인수와 with 로 채우기, C# 11
using System;
using System.Reflection;

[AttributeUsage(AttributeTargets.Class)]
class TagAttribute : Attribute
{
    public required string Name { get; set; }
    public int Order { get; set; }
}

[Tag(Name = "first", Order = 1)]
class A { }
#if BAD
[Tag(Order = 2)]
class B { }
#endif

record R { public required int X { get; init; } }

class Program
{
    static void Main()
    {
        var tag = typeof(A).GetCustomAttribute<TagAttribute>();
        Console.WriteLine(tag.Name + " " + tag.Order);

        var r1 = new R { X = 1 };
        var r2 = r1 with { };                // no X needed
        Console.WriteLine(r2.X);
        var copy = typeof(R).GetConstructor(
            BindingFlags.NonPublic | BindingFlags.Instance,
            new[] { typeof(R) });
        foreach (var a in copy.GetCustomAttributesData())
            Console.WriteLine("copy ctor: " + a.AttributeType.Name);
    }
}
