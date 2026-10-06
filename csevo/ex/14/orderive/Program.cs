// 슬라이드 p14-v13-or-type — 우선순위는 선언한 형식 안에서만, C# 13
using System;
using System.Runtime.CompilerServices;

class Base
{
    [OverloadResolutionPriority(1)]
    public void M(ReadOnlySpan<int> s) => Console.WriteLine("Base");
}

class Derived : Base
{
    public void M(int[] a) => Console.WriteLine("Derived");
}

class Program
{
    static void Main()
    {
        var d = new Derived();
        d.M([1, 2, 3]);    // Prints "Derived"
        ((Base)d).M([1, 2, 3]);
        d.M(new ReadOnlySpan<int>([4]));
    }
}
