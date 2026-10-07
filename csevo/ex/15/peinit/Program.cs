// 슬라이드 p15-v14-pe-init — 생성자 초기화자는 구현 쪽에만, C# 14
using System;

class Shape
{
    public Shape(string k) => Console.WriteLine("Shape(" + k + ")");
}

partial class Box : Shape
{
#if BAD
    public partial Box(int side) : base("box");     // defining part
#else
    public partial Box(int side);
#endif
    public partial Box();
}

partial class Box
{
    public partial Box(int side) : base("box") =>
        Console.WriteLine("Box(" + side + ")");

    public partial Box() : this(1) => Console.WriteLine("Box()");
}

partial class Pair(int a, int b)
{
    public partial Pair(int a);
    public override string ToString() => a + "," + b;
}

partial class Pair
{
#if NOTHIS
    public partial Pair(int a) { }
#else
    public partial Pair(int a) : this(a, a) { }
#endif
}

class Program
{
    static void Main()
    {
        new Box();
        Console.WriteLine(new Pair(7));
    }
}
