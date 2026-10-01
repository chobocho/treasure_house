// 슬라이드 p4-v3-ext-instance — 인스턴스 메서드가 언제나 먼저, C# 3.0
using System;

static class E
{
    public static void F(this object obj, int i)
    {
        Console.WriteLine("E.F(object, int)");
    }
    public static void F(this object obj, string s)
    {
        Console.WriteLine("E.F(object, string)");
    }
}

class A { }

class B
{
    public void F(int i) { Console.WriteLine("B.F(int)"); }
}

class C
{
    public void F(object obj) { Console.WriteLine("C.F(object)"); }
}

class App
{
    static void Main()
    {
        A a = new A(); B b = new B(); C c = new C();
        a.F(1);            // A has no F
        a.F("hello");
        b.F(1);            // instance method fits
        b.F("hello");      // instance method does not fit
        c.F(1);            // instance F(object) fits, so it wins
        c.F("hello");
    }
}
