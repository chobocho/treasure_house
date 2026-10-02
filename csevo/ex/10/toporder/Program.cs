// 슬라이드 p10-v9-top-order — 형식 선언은 문 뒤에, C# 9.0
using System;

Console.WriteLine(new Greeter().Hi("Kim"));

class Greeter
{
    public string Hi(string n) => "Hello, " + n;
}
#if BAD
Console.WriteLine("after the class");
#endif
