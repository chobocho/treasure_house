// 슬라이드 p11-v10-rs-limits — ref record struct, C# 10.0
using System;

ref record struct B(int X);

class App
{
    static void Main() => Console.WriteLine(new B(1).X);
}
