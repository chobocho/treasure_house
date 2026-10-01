// 슬라이드 p3-v2-constraint-errors — 제약을 어기면, C# 2.0
using System;

class NoDefault
{
    public NoDefault(int x) { }
}

class Base { }

class App
{
    static void C<T>() where T : class { }
    static void S<T>() where T : struct { }
    static void N<T>() where T : new() { }
    static void B<T>() where T : Base { }

    static void Main()
    {
        C<int>();
        S<string>();
        S<int?>();
        N<NoDefault>();
        B<string>();
    }
}
