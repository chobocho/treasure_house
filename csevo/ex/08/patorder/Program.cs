// 슬라이드 p8-v7-pat-order — 앞의 case 가 덮는 case, C# 7.0
class Rect { public int W, H; }

class App
{
    static string M(object o)
    {
        switch (o)
        {
            case Rect r:
                return "rect";
            case Rect r when r.W == r.H:    // never reached
                return "square";
            case object x:
                return "object";
            case string s:                  // never reached
                return "string";
        }
        return "null";
    }

    static void Main() { }
}
