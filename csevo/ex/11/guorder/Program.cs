// 슬라이드 p11-v10-gu-order — global using 은 using 보다 앞에, C# 10.0
using System;
global using System.Text;

class App
{
    static void Main() => Console.WriteLine(new StringBuilder("x"));
}
