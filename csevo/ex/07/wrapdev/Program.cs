// 슬라이드 p7-v6-wrap-dev — Roslyn 이 지킨 옛 컴파일러의 동작, C# 5
using System;

class C
{
    public C(params int[] x)
    {
        Console.WriteLine("C(" + x.Length + ")");
    }
}

class D : C            // no constructor: calls C() with an empty params
{
}

#if BAD
abstract class Foo<Item>       // the native compiler rejected this
{
    public Item this[int i] { get { return default(Item); } }
}
#endif

class Program
{
    const int Zero = new int();     // treated as the constant 0

    static void Main()
    {
        object o = (null);          // parenthesized null
        const string x = "pass";
        string y;
        string z = x ?? y;          // y is never assigned
        new D();
        Console.WriteLine(Zero + " " + (o == null) + " " + z);
    }
}
