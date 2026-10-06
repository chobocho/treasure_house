// 슬라이드 p13-v12-al-global — 프로젝트 전체의 별칭, C# 12.0
global using Money = decimal;
global using Line = (string Item, decimal Price, int Qty);
global using Lines = (string Item, decimal Price, int Qty)[];
#if CHAIN
global using Lines2 = Line[];          // an alias of an alias
#endif
