// 슬라이드 p3-v2-constraint-order — 제약을 적는 차례, C# 2.0
using System;

class App
{
    static T A<T>() where T : new(), IDisposable { return new T(); }
    static void B<T>() where T : IDisposable, class { }
    static void C<T>() where T : struct, new() { }

    static void Main() { }
}
