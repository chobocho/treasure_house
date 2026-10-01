// 슬라이드 p3-v2-accessor-indexer — 인덱서에도 접근자 한정자, C# 2.0
using System;

class Grid
{
    int[] cells = new int[4];

    public int this[int i]
    {
        get { return cells[i]; }
        protected set { cells[i] = value; }
    }
}

class Board : Grid
{
    public void Mark(int i) { this[i] = 1; }   // a subclass may set
}

class App
{
    static void Main()
    {
        Board b = new Board();
        b.Mark(2);
        Console.WriteLine(b[0] + " " + b[2]);  // anyone may get
    }
}
