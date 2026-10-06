// 슬라이드 p14-v13-fk-local — 접근자 안의 지역 변수 field, C# 13
using System;

class Box
{
    public int Size
    {
        get
        {
            int field = 3;           // a local named 'field'
            return field * 2;
        }
    }
    public int Fixed
    {
        get
        {
            int @field = 4;          // escaped: works in C# 14
            return @field * 2;
        }
    }
}

class Program
{
    static void Main()
        => Console.WriteLine(new Box().Size + " " + new Box().Fixed);
}
