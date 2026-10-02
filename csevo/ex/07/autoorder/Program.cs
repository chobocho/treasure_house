// 슬라이드 p7-v6-autoinit-order — 초기화자가 도는 차례, C# 6.0
using System;

class Base
{
    public Base()
    {
        Console.WriteLine("Base()");
    }
}

class Derived : Base
{
    static int Log(string s)
    {
        Console.WriteLine(s);
        return 0;
    }

    int a = Log("field a");
    public int P { get; set; } = Log("property P");
    int b = Log("field b");

    public Derived()
    {
        Console.WriteLine("Derived()");
    }
}

class Program
{
    static void Main()
    {
        new Derived();
    }
}
