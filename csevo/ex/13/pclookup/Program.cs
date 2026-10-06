// 슬라이드 p13-v12-pc-lookup — 초기화자와 몸체의 이름 찾기, C# 12.0
using System;

class C(int i)
{
    protected int i = i * 10;  // initializer: parameter i
    public int I => i;         // body: field i
}

class App
{
    static void Main() => Console.WriteLine(new C(4).I);
}
