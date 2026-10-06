// 슬라이드 p13-v12-pc-shadow — 기반의 멤버가 매개변수를 가린다, C# 12.0
using System;

class Base
{
    protected int x = 100;
}

class Derived(int x) : Base
{
    public int Get() => x;            // which x?
}

class App
{
    static void Main() => Console.WriteLine(new Derived(1).Get());
}
