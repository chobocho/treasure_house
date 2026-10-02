// 슬라이드 p10-v9-rec-abstract — 추상 레코드와 복제 메서드, C# 9.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

abstract record Shape(string Name);
record Circle(string Name, double R) : Shape(Name);
sealed record Square(string Name, double Side) : Shape(Name);

class App
{
    static void Clone(Type t)
    {
        MethodInfo m = t.GetMethod("<Clone>$");
        bool slot = (m.Attributes & MethodAttributes.VtableLayoutMask)
            == MethodAttributes.NewSlot;
        Console.WriteLine("{0,-6} returns {1,-6} abstract={2,-5} "
            + "newslot={3,-5} PreserveBaseOverrides={4}", t.Name,
            m.ReturnType.Name, m.IsAbstract, slot,
            m.IsDefined(typeof(PreserveBaseOverridesAttribute)));
    }

    static void Main()
    {
        Clone(typeof(Shape));
        Clone(typeof(Circle));
        Clone(typeof(Square));
        Shape s = new Circle("c", 1.5);
        Shape t = s with { Name = "d" };     // Shape.<Clone>$ → Circle
        Console.WriteLine(t);
    }
}
