// 슬라이드 p8-v7-throw-where — throw 식을 못 쓰는 자리(문법), C# 7.0
using System;

class App
{
    static void Main(string[] args)
    {
        bool b = args.Length > 0 && throw new Exception();
        int c = 1 + throw new Exception();
    }
}
