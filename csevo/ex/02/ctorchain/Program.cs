// 슬라이드 p2-v1-ctorchain — 생성자 사슬과 필드 초기화의 순서, C# 1.0
using System;

class Base
{
    int b = Log("Base field initializer");
    public Base() { Log("Base constructor body"); }
    public static int Log(string s) { Console.WriteLine(s); return 0; }
}

class Derived : Base
{
    int d = Log("Derived field initializer");
    public Derived() : this("x")
    {
        Log("Derived() body");
    }
    public Derived(string s) : base()
    {
        Log("Derived(string) body");
    }
}

class App
{
    static void Main()
    {
        new Derived();
    }
}
