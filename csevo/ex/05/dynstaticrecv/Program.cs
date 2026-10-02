// 슬라이드 p5-v4-dyn-static — 컴파일 때 잡는 것도 있다, C# 4.0
using System;

class Program
{
    void Instance(int x) { Console.WriteLine(x); }

    static void Main()
    {
        dynamic d = 1;
        Instance(d);          // no 'this' in a static method
    }
}
