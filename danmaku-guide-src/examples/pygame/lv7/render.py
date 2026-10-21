import base64
from io import BytesIO
import pygame

# Noto Emoji 로켓·외계인·탄환 PNG: Apache-2.0, 고정 출처와 원문은 같은 폴더의 LICENSE-NOTO.txt에 보관한다.
ROCKET_PNG = 'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAGJxJREFUeNrsnXtwW9WZwD89LT9ky3Zsx44TO86DJA2JvYGWUNLYLSy000LC7NCFnS52mXaZ2XYIO7vd7fJH4j9gdtnSwM6U6bbbxEwHaGcYSOgMpexsY5elPEKwCcHOw07k2PH7IUu29Zb2fMdX8tW9576kK8eW9M3cubZ0JV3p973PuecC5CQnOclJTnKSk2wUQ+4nWJty8WBDI9nVk62Re6iO+x+lh2xz3L5zR9dVV04B1jZsB9kdIttesjXzoKuVdqIEx3IKsPYsHKE/kATwBJlcBBiYhfbWfrES5BRg9Vl6K9keTRU6Xwh8VAIMA5uJEiSEA3Om/6jRaBR/1DfIdthgMLhWsbU/wcFniqWwlO5DPg9EwyFN7z/ro7tYGOnIKgUgcpyLm7hvW2XgD3Hgm0Wu2WSGPHsFWIsr6D6u0AT+7MCHEA76VH3GYpAoTST+78GsUgBi/fU8qzq0WhSAgMdzOsrL2peB2OyQX74RbI5qdtZOFMNgsgCoVACM/zwRf16GQo990Qd4TznIc0e40ghIOOhcTeDRxRdWbI67einxTg/RMKBWZrwJ/zZntAJwgI8rhIPYsbhrIorQs0Ku/ngq4NH1e270gt8zqSn2+8Pyx2SaB+jQkEH3pBs+l9wdZ1meWvAoCB3ha03+BNaf+QqAWT6x7Bby5xkFJUDwLWku59DVHxE+Z7LYwL5hlyrw6Ornx65AcGFW8zmEI6L4nxUeALhSr4kowjWWy+WkJV0lIYGP1n5S+NmYvBWUb4ICYvWKoYxY+vzYZfC5RlNq/qiRjKwCuNq/XuYQ9A66JoHPvXGGWv30a88eKR++JHL3aPVo/Ypl2+Q1WJy+rtndC2V0nvmwKysUgBVz06kABL6k1RdWNNCyTknQzWOcV1vfJ5n89WSLAvDjP4Ju55QCmy4ObtPN6vmx3l2xCdADqLV6tPSFyau0vNNLJKw/qzwAavopsp0msb6DpwjHSHhoZv0QScBv5Kw+Idl0V2yEwsoGVbFeT6uPf75/aZOQT7NCAQj0U5wCsJ7r1AE+s99gNJnA1vItKLgxuOJWrzL568wWD5AW4Vw+Wv0h4XMF9iKoaainSrBQWQOFEyOSpZ3nRp+mbp5awbivoACiHMCYw6rJ5Xez4JdXr4fabVsofJSJW/cx3wMtfnbgo7TARxl2y8MXDgXnFEA9/FYOfr3Q5aPVl1dXJbphgQKgy3dfP09r+3QJxn2t7j+nAOrgn+TcfoLk5edD3c7tUOQoEbv5vPy4F0Brx+FbLT38pKxf2al0MXOiHGLZeM9sKReXl0FlbU3c5bMkb24Wdj3992m1er71907JHuIi7r805wG0x/tGVrxfX7dRFn4kHIZr03PwWXXdipzv4JziIaeknsgpgBj+Ic7yRfEewQvjvSgT93phsO8yzLvm4Mod90MwryCt54txfyGoeNhpqSdMOeSiZO9VstmE8Ddu3wKFxcXyrnh6Bm70X6MegHoCswXmy6qh5vJHaTlfHPG7OE0+J6ro/ttyHiCFZK9h9066l5OxwSG6CWV8SxPd0iGjCwnz/TS7/1wSuJzsYVevVa65Ixfvhy4PUNcvJRb/IrSc+Ge617Pp0z2m6tAm4gF6cgqQRKaPMV8p3iP8mMuXk+LJITjw8jHdzh2zfpmeP7/5I+t+jDn4ycHHeK8WPj2+YiN8+pff1eXccbhXBXyUF5QOMGcpfOZIHgqCRwWQk+nRcbKNaf7c4V1fpvu975xIKfEbUDdDzKUU/7OyCuDgi8o8tfAx0XNNJN/Vw/kCBe5pGhKSkSG3auv/OXH/p5UOWvU5ADe9CxM03PdwQ72pwndohY+ufuSqExY9ibMtCq1mKMizgGvRD8FwRPW51Pa+p9kTqOj48QWvA3SuaAggsDDLORiLP6nA4kkjD1gj+YwPyPuO6QUfM3xs6yrBj2X6CHxrZQlU2PPBkW8VN2bmfTDiWgDntEdWIZIJByo6fjHpUANfVwUgYLCU4k+DRlidaZh9a9MTPjZ45Gp8hD7mHAJzOAh76iqgrtwu+1kVRTa67aouhSsTc3STUgRUAgwJd7z2rGKJiIM9Kjp+MWlXe6BBRwVgTcNuSXUGDhcCDnHvjdb/9krCR8svL7DCnQ1VYDFpL5pc3gB87Jyge7k+AXqCqoFu5vN4gef5CU3W35YxCqBTwpc0/PV2G4UvlHfPdsPFASdMzSw7uE0b1sO+3Tthx5bEnwE9QNflEVkloEG7+39g2wdviryByppfU+xPhwII58lhwta0luEXW01wcHtNguWfu9AHL5/+fQJ4oWyqWQ/ff/hBuucrwVsXrismigh/V9dvaJJIqw6SczrVx37mKiArVgVwM26bU83WVwN8TPwQPsbzmCD4P/zpfdXn8b2/PgwHbl+2AUwO/3x1XNVrcWr5pvdOw8gnl9T0+1HQ6ptY077WdBm4kqUeHz5m+Qe3LV+jj+BRAbTKE20P07AQk64rozDp8aojOjoG13s/gz19n8DGESdYg7Ih5DCBr9noTDn4Yvi0hKktB7ttqcxDd/+TX/46qXP67FI/fHX/7WCxmOMWNzKnPCjkXliE8wMD4DNZYKimHq407AK33YHz2qHEIzLyUwR+ezLnZ87BZw/q1DgKl63/3feTPq9Fr48mjPd+Zf/y+w4qdxIRfjC0fH1gwGKFgbrtdEOpmhqFMtc0FC24nTsGPk965ZOMGAx6/MWXHb5g4A0WfASvFT66f75g4peKfHLh4nKSRxJKVgMpIet3DhIPsCB7zPi6aujbuhvO7r2zTWvczygFQPho+Yt+f73oy3FdPi3wY5D4Ipfxq+rgjSRe5m0xS0fe8ZlZEvtVXxb+/P8+++OUyuw1rwBWsxktv9EfFLfJSojlS03mkBvLV7LQZMKAGgmGwtT1q5QeLR2/jFSAH/zXb04GQqFmCpShAMnAp8ACoZvyfT65dCkh7itIG7F+V9YqwA9/8dsjoXC4dbnREqabkqiZxbOgswLwG0JScmV4GKbdbtUNHwJfl/WN1qQCPPnfrzUTSxFdnbvgS3S13vl5zfBRcGiXLzu3bE7pfOs2JK75J+wDYNy/MjSs9u06Cfxjev2Wq74M/Gh3EyZ3jdy217uusv6sLa+xPyBujnvJY47C5fINx+5xAkdJeSkE/QGYGB5RNYUL27XYt4/lAnfd3gh9A9eS/g7CbmDCOfv9WuI+unxdF7s0ryLQDh7oOm7fLDyu76HvgKGwCCykTBK6/HniASKRCBiNy44N5+7hplX6J+bgtrqKOMA33jmTVDWA3oM/OCRsAp27dFlr3HeueQUgsGOg8Zc5yO3rlV539RuHYKF6A/0735oHQa+4o+Ymbp7vBZIVnNCBY/oF1qWf6EjbI/DMiydUZ/QoBfk2Oh7ATy7xfePNnv4BxXpfUPLpPr5iSDPoGFi05L2QeIcLTTK9czf0PvJdHuhFGHeJLdJCMv/6yipdzh+7dvyh4OsjY6qVYF2ZgyoNPwHkjwMMT05SBVBb8hH4aRlZNafBsh/luXJdFmMK2fLh8oMPJzxWlGeDcWb8DpNcIEA8ROq1PMZrnNGzrbIkns3/9Kl/oK1hHBxiKQJaPbZ97z2wn/4dk97R2Th82ufv1xT3D6fLSA06wz+jF/QwRMEfCYMvGoYb33kcXDtvFXfNiAdwM8IAhofa8nLdfqS9teVxJeALTgiZJBn81KwLCmw2mu0LJ4OgDBK3f5br/2PS93/nP9MS9w+nw/XrqgCpwl+MhCAQjRDYkTj08NJizhDccgu4H/8R83WY9I3OshO82vJ1ungBfji4nSSFWqaFYTWBlo9ehP4fCsOHvb1a4n67niVfWhRAC3wEG0TQJFOPQcf/5WT2X/8dIqXrpJO1iXFmA0hvL7CUXxipJ6gvt8eTQynwGD4QPr+phBn/+IzqigTr/RZIs5jTBR9he8IhHvSw5vf3HbhHFj6Kg5SEk+45Zk9Ar1xAaNG4YY/AUZAnUgScFs6a8IExXwP8nnTGfV0UQAn+YGAh7saTkWh+ASzec3/CYziVCxs5wcDyzJhi8tj0vIfW/+IcYVa3ikCUmXkDipM8Y4IZP25amj169PnViElv+J5IEIaDiynBR/Hvb4bA7qXKBwd1arc1wDqSZJVWVoB3fiGuBAYDRrEotXahRMg54NMYDm6WaCz3UB5OdYhXixj1hO8KB2AokDp86sIP3B2HjxM584uKluM7728aBgoKE7p/Cf0Dj4c5UrgSguVen3NQy0ueTGfGn7ICKMEfCXp1OanAF5risR8tXml1DoRfKtP9G59zMUNEuuFjxq+h3Osg8J9faSU16gEfwesFnyoAz/WXVoqTQOEoH0pZkZ12AZnhhHiASfVDral7L1Lra4R/isDXPMgTjUbx8rtm7uqp9CmAEny0fj0FPQDt9jlKRJM6MAkUXqEbkyqH9G1YsGHkUl9/J18pkFpf4wAPZvzJwMfL5bo5LtdQGdKiAFLwsVM3RJI9veGHajbSCoAqQIl4VS5cfk1KsOQrsklfO4rlIqtzqCd8jY0eeu+iJDP+J/hpEDDWME5ZAeTgY5nnCeufXIW27FguURiTJ3F1DjmpKnFIJoRLpaErLUqQBHxXCvBpDyytOYAS/GQaO2okXCrdvUP4wUBAMSGsKZVf5UNvJbgJ8FFwQmisYsB9UgmkWQt8PRo8igpQsyn+96JnIV7y4aQOtevyYCgot9tpCSinBEuNpIKbBT+lOX0GgwE9QMrdQvNqgk8VoKycZ/Fj8Zgvtw6fUGyuGdg8OwtFJOZPE8Dz9mJJJYhEoklPILlZ8PUUswB+PQs+dvcw2083fJrlC3r/WsCXXBuAujN/IPt+nuJG4PRDfwsLFeslE0MsE6scjqyDLxUCHOlq8KRL0OIb3joF5X0XINFrRYjXWgRLQH51BcwH/KEgVJPcwWJS7o7HLtxc6/BFSeAXL3Q7gXdfmZsAv0PrCza8/ydo+tlzkvAxacX+QJ7FIvs+6AWuT03SOQZK8DPB8uWqgJdiDZ4VhI/gN99oe6wdVN4x0+zzwq5XTlDLx7+l4NMvWVAItSS3UFICbBfjBBPcWHMMZtxurR2+VQ1fSgFOpaO7JwceFzUi8DH0dEdULKhcOHqDafUs+NhUwuYSloeb1lWoyvrRC6A3mJlfriJwVO+DzzMLPq0mmFS2NjTD0h0xm9P0uZ1ka4stZvT000/HKw/L+s1gKquWbvR0n4Xtr7/KriAI9H7/Qhw+de233QnzD7WJYj6ODagZIMKcwDMxDkMeTX2DNQFfUgF4ilDPKUKrjuBxIaPO2AMEPn5Gdyz5NNlJIrZxB/PFCB4VQAo+Wr5PMMVs9sf/RioLcXMJXTyWgV6ZBDFMrH2UeBnP5AQYzBYwlJSB0V6C3aaMgK+oADoqggg8B5+5Ynfetn1gsOQlxHuEz3L5cvBZ1i+iRZI51owiH3lstPcC3ScGTRMYS0rJVsZShDUFX7ITKBTOVbcRRWjXqAhM8Dw5CowLRcKuCTBXbIzD33PiRRr3tcBnTSljCTaBCm02mHLPxSuAudERGL9ykXoAcaYYhsjsFN0MhXaSYBbRPVGGNQdftQdIwiPIgvf2fQtzi8afvn7HcanPQC+QT6xz1ysnNcOniRyxfPQAWsS9SOr7T87CzKDmC0F7zA07WlZqHt9NVwAZRZAET6DHjj0Ui/c/+93tpP5mN16KvUHY9/Y7ohJPDXw1rl+uuRP1zFELj4aURzsNFmtPNBho6XrtpTUHP2UF4CkCAq1n3ZuGgHdw4I8In3vzg1ugf0Q8icM+64Lb/tgF5kBQM3ws+dx/94/xOQVqBNfjwwUahCWeoiKYzB1dv/1VG6xhSevFoQQ+xndcw6ee9Xz/SBlRgu26wUfoCB+VQI3E1uRRmq8f9S0uKYNnjm/5T3a++svnYY2LOY3wMSwcB5krhrbWzEBxgZ/E3ryU4cfivlr42NVTO3XLYCugm7G8CswzE/C1c109P/q0Z83DT5sCcPBPyv6oJjv5Uevh1l3r4b2PZ1OGv3D/tyHwhUZVVo/uXsNSbHHZOHYd7jzXhUu2uiBDxLzS8A2WcjAW3wkG69L6fV/+EsDghzdgWwrwMenz3XW3Kqv/tH+AztrVIrhG756+c7CzP96H6MkpgHTMlyztjPbbwFi0L/E1V0Zh91t/hHCS8NHlK2X8amM90+pHnHDb+Q+gaDGhITSXUwB2ts9crhWMVjCV3U+tXwj/yg9PQHjelzR8TPqSyfCVBIGju6+aHJXqc+QUQCAnmdl+muBHrFZwP/KYZLmHS6/1Op2a3T2Cx+XZtwxehmwQg07Wf4iz/hWDP3Xf1yFUUUlHDmNtYxQctkWrd2u8CARX30boasC39l815DxAoutnxn1T6b2a4VPrDfkl4dNk7qtfg2BZGQ7XQWhyiI4djIENLru8mlw9WvvGkUEKvXRuWu3LdK0AuCt6jnKhs8tgMBxbayHgCMv1Y8IXy/Tjlk2gDz7zhiz8kZAPXDIXnMzedQD86xMneEaDfqgCP5STaDAZNJDXE0ohg9MbSTwvtHJrwE/360ls1wCdLz06wo+NhsbypmbuVnuda0IBOOt/glnqCbJ9hI6Wjx4gFfiLW7dKfxnimKutUaimkKItG07+inlb+BRFTw/AWkmteSWTTKMO1i/K+rHOF8rg06+nFb7AQhG+IxX4JoMBKsw2cJhES8x8qlsCtmTpTmHhspIhwKi39RvzbxG5/sFnXoe5d/uShv8X//Jt2HDPPtXwn3rqKRfr3NRKmTkPtubZiQLksRax0hsQXt1zirP6dqIUHWslB2gVWT/J+o32RFAzv++Gmbe6k4a//+gj0PDNLwLed2voxjycPXcR+ocssvC50UnN1o/WjtAtBmNCRZJOBSDAV2xBKL0VQGz9hXtwUl9Cxo+uP1X48a7chiKoyXPC3Nw8HUkcniqGoclinFOA1nOYs3zJ0KQFfEwYF8E6IYMkqXqWm9FzRmj95oq/oftY0vf5Xz0nmfFrhb/0ph4ITbwiOjZ/5+/i34Oz/mtKCoAx3m60SIKPSa9vLmN7AKl4gEdZsT8GP5b06QofG0BeZpPGqRiaBNDtJjPdKwkuZpnJ1p+UAnDJX6vY/S+v5YsJn1TSJwffas+Hr/zHY1C1j53tRxcvsR7ulAtNhUYzFJANodsMKd8nM6cAwFiKhFo/L/YP/+dbScG/++c/gNLtG9jwvZcgGmZe73+a5/5b+U0ptPhaawGYkux4L4jjf09OAQAeECUSBYnTukxF+aJ+iRx8hI7wrXaJ5eAiAQi7/8y0SBL/+evqHeU/WUXqeJO+s97mMk0BNPUBOPef4AHozB5B3V/50H7V8GsP3ioPH/kj/AjzWsV2KevHxI7RxNEkuChGpnsArY0gkfs3FIrX8S/7ehOUHNipCH/P9++Dgz95TBY+uv6I95KU9XdIJaYbLPkp/zgR8YIYrmxXAJH7N9rqmQfWPfUgzG8uY8JH4Aj+1u/dJ/th0eA0hF2dUk+38awfy9JmYeKXqgQEXUCZK5yyRgGaE6wfh3p5yV9iHmCDL734OOx4+KAo3n/j5X+irl8R/sybUk8/T6y/UzL2W2y6/DhK9zLIqkYQq/nDmuPHzKZHZ+D8L96GopoyRatPgM+O+50EfovA+uPnhXG/Rgf3jy3gS76E5WU7iQdoyTQF0OInxdm/tVrVCwury2hzR41gzJdx+6y++RP8sg87e3oIroiW6fFfqwKIE0BrjUwGFYBoYASioWli0VP0f0NejbTHIM9H5j+GyMJncvBbiPVLgigzybd11QqukMIYA3ghaxWAm+5dL4r/LOA+59Ke0bTBxw159aLX4uMRYvUSjR4l+AjmEFp/mTn128OM0apFFHraMjEB1OIBjrIt9hxAyEOsfIrGbXXBlUBGBSB7Cn7xMt3LCDZ62qQsH8GQPKCnymxrTLXpg+BnQqJZxE+Sz+jI2iRQzWVeaZR2Av6Y0kGv33JLa62l4GSq8BmronXgAlZZWwVITvdOvzg5q1ftdj/a3XQNVNx/mCUSy+BmPHw1fYDjKULU6jpdnNVv1gKfk5d0hI85x5OQBaKkAFpuYNTDAccfrgkhYjWlBTzZNqtx+VLNIa2lGtb6jDWQacJJrN+VDQqgJgdoBPbdKFzcj+Ui0HqSDB+oYKcFPf2khYQB9FhH1MJn3PcAv9PmbIGvqgrg4CYzCoY/YifjMZxW3ZmEi1cjL6hVgPGgjwW/JZvgq/IAa02IF8BqoFWp0cOo9ZtYaxxlew6wFqVdqdyTaPRkHfyMVABuyftODbV+WyY3erLRAzC9AJZ7DPjPZzP8jMwBeLkADhE3y9T6WdHoyVYPEPcC9AaX4htad+bgZ7gCkFyg0x+NdKLlC2b23NRr8XIh4CYJt64xbj3ZVuvnJCc5yQlb/l+AAQDc1eCtPYL6kgAAAABJRU5ErkJggg=='

ALIEN_PNG = 'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAACeVJREFUeNrsXU2O3EQUrkI+wBxhjpALBM2wDUIICSmKkCYIRDZsImWfmX1QxDISEkERURaIBSIrFtMoF5gj5AjZkdU83G2X/arqVbmq7Bnb3d9Hmrar7Xa7vu/9+JXLoxQAAAAAAAAAAAAAAAAAAPsPPdeB3z5597B+O87d796zu+dL7tD6vEp+36Y+r80cv7easa/O6tdJwX7nCzeqp4X7zSKAT+AEDxsQAAQAQAAABABAAAAEAEAAAAQAQAAABAAcAqq1/eC3T96dFOz2/t6zu+8zj3OsCgarIIBE1IScFpJ/WXC4C5U/iPRQlQ3snM41socQAEAAAAQAQAAABABAAAAEAEAAAAQAQAAABABAAIALa2rY7z/8/VArfaZ1/f/dSzXvqllXpq1bb5ZrPP7y58+ucg789sm75/Xbnczfe1Swzxbv21cOjlXZaOC2Hz5k7vPbvWd3X+bs8MeP/9xRRM9J1f9R/7q+5uvX6nr7Xrdd18tt++PvX33dcWWPBlJ9wppOLH1Q/U+btXZl10z1ptpI6Kigo7ZEntyS0EvJVIXnlYt/83eho13/kWo4al+GyIah9jPVftBsdBQJAc2mxL6Q2Be2/5qtiO8BzAFiL7ulFYNRQNtgbysIgIjvSTbxXAyOECCCmdh3eVK2JyDLCyQlgb1KhryAtQz+Z+WfhBBAluUbcTS5wYAHCKgr4AVK7d/9IUC+BGT3T4w+5gEC/V1JX8oTQL6qO+I1W98ulJG5+1Faz/eUisVYMhX0nQq7f1JiEih5gMr9Uq2YT9f2L7WJN+vt1UBxD9Q/6kBFQLHgnLK35/6pc/8kuP9BD9Dbv1bKje2G+F27bq8GqV0e6c5bV7WrLRwK+WNDoBCm7Rzed//SMSv5S/0yUbOvKQjQzut3HoGm65RDEMEU+U9PruT6x3iAgDvXjGUiJxTowk4QXP++i2C65Jf4NZtDfFoCKHgAYlU/JwowlrV2kkEq7g0x/lObjOxTZhAioTQPcOO/7fodD5B6FdAngYplA3ZC2IWCkR7AFZ1Hdpu97oM3CJI/yhuQkANQV8wjU/ljYSAjCeSNWgwFvRDKrgJ25LJkM0S26ST22aagt7b1+dzxiu2AzlXBsU5SCB4bCmQPYIeBWPIXDgFe7OdhoHcFvRAKY4BAesz1m5P4/KdPS6aUXar8gaerwulrFCVecPlUVAdwY79r/TQY/wUPsOWSrPS/sVQlh4Edga0IxrhHnges3PXnWH1pEcitA5gF1/rNUHG6AFoyLIl65Dakd9bvXCHkFTJb4oU8YJ8SQdHqRxWBTFm+t3zf+inJs1SD6tWuZLUlhBECbrrBWL8pWQreYK1CkIm3rb74KoAVASiSAI4SQIT70SGgCzSu9UtVQSaEtRIvh4ARXoBky+8y/0TLrMRqXG/j3pIVFUaEgL7moNuqom39Ygig0r66vZFH6Vgu0fYNNWUn5oYAxW4LS0n+gh5ga3nk9jjZvsDiv5QUZS4eeBhokxgvLOxHCJjK/Xd1QG75pKz1VFRJ1iKbfxMEtCqtBfeu3yOeeQcuhFWQ7mf2/B4Kd5tyD0CW1fPLvhyPV2W7TO3kAIVOwHgAy/VbojDegQlhDCnqllIIoiDxvvsfnwO4IsgNd1VR3HREUNSzVg4g5QOOEExVagQpNKsXmN4D9FVAyrb8QQHkiECrwjoANfs2xURtW7yV+fceYk2FINH1T+QBuiSQ6OYEkC6CshPg5HehwHX9znp5tTGU1IQCxtiQk0b8mDpAbtGnSAA3JgJi5GsSQ4EkhNGJwA0Hg0EP4Lp+UsU31Y6xfNEUXjx4c6wCM2j66WLspZqpYlVVXTaFG92G6X5qmd3G3LmJ8U6blfC59wpICWFKkqj909WDtk+DWpGTvKHEzyWe+vv5SLFxfPszE/MVu+T7+PG/0+t8AVw9en3/Q4ovTMar7/6ihv9eFCrn3SXSE4K0HiCehYops36yy5LZQpCIl0SQ8m7c/je/fDH6FKtpOocldFZo0LsqIUnv0rbG5fNlLxyYz/nVgV0z8HLr5Pgv+AIqsH7vo2Hih8TQx3r+2XhMIwBybiR1CQ7mDo4gQkKwvtcRAxdIyAuMjP8UCQnSZ7dh/YsSQHdNf2NeYEAMLukUuMLWRT4/SQzDmf+01j9VZXR6D1DsBey2rsDEag1BMbQFI83pkdx+Qs2KQi00nBPIIYC8cJBKfEwIyxSAdElo2gyxmgKjSLZg+i1sr9C0+GLwiCeeCNKoC0CKiKEk7keJ51cB/J0LQE03wjmRANyKOzli6Mnt9NDeRyBZfygfsAegHNF4xMcSwbIwEBJC0PKddWv2rjN/T7Z2gXRWAVyOAJxsmFtvms1JQvCXRfJjxIujmIUKoLgQYiLgBjJE/KAQFikAonhl0AoDMV0EmFeRnEAamfTuXFKWJPPzP4qkBDHSQ5af6P4jnmC5AkiuFJt8wK049p0nL/tisEKDQHzw1rYst+8LwSv6krSeYPmhuO+4/fUJQGTfbZSEEPIEqV8rBCFdUAqguAhkwlO9gEt4JO4rdgPI2jwAWSWZjB8taiBg/dbdyQ75WiI9czSQykRgWXvQ8l3iwwKQlpdRCGr+KBO7HOwZ6fJ0Fv9bgz9T7sBTikai2wjki8RTuvkPiKBIAL7lb9T2UXGi1dtJ35TkTz1ekoVfz/68rI9+oruJpoqN/rG22HLf5J2O1lOcKgmXu0IFIJn0oAAuvn351fkcPMz2Z+Nu9FZt0fJHzWARyZ5QAHPRsAQBuHMRlzb/Y1oBkPPgRmlC7oEI4HpiqqUKZGbwo9sTQGcAhyqAayKxPiRfQaRaqp7K2GMFYP+eA3c4esjqVdrc/cPLAfoJgx6Z5OTwmrUMiydRHJRKfoRwj3TJ7avBhzftvQCkkzdPDQmTl0Ak2yS6NaUUh4R7CpIEIC97Vk/zz3daxF8Pj3mDEP2yF4h5DkEONOwOZKfgEEcB67fIXo7VL04AkhjsZwiRYk+l6Ja7CabaEQVpJU0q1kmTxGjAIZDnEayWAetfGiq1YBC7hz4cBKSAITt/XwiJeaBEbqDNmhewgplMlVoJ3I7Vlhcgq/RnPetIZ5KcavkD5K8FlVopvBk4zhNGje/QpNXYqcVSqrYvj7uv1B4h9nSO7KeO0WH8HZRVPXbjxYM3J/XbZcGuF49e3z/PPNZ2+6cFxzqtj7VZS5/i7wYeOCAACACAAAAIAIAAAAgAgAAACACAAAAIAIAAgL3HbKOBLx68KflDTltcFOyzuaV9triszy37nHIHq1YvgFLcVke1I3qbAmE/XVN/IgQgBwAgAAACACAAAAIAIAAAAgAgAAACACAAYO8x51jA1Z726aZgn/eQIgAAAAAAAAAAAAAAAAAAN4f/BRgAARuHSArdBAQAAAAASUVORK5CYII='
BULLET_PNG = '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'

class Renderer:
    # region renderer-init
    def __init__(self, screen):
        self.screen = screen
        image = pygame.image.load(BytesIO(base64.b64decode(ROCKET_PNG))).convert_alpha()
        self.player = pygame.transform.smoothscale(image, (24, 24))
        # region enemy-images
        image = pygame.image.load(BytesIO(base64.b64decode(ALIEN_PNG))).convert_alpha()
        self.enemy = pygame.transform.smoothscale(image, (32, 32))
        self.boss = pygame.transform.smoothscale(image, (64, 64))
        image = pygame.image.load(BytesIO(base64.b64decode(BULLET_PNG))).convert_alpha()
        self.enemy_bullet = pygame.transform.smoothscale(image, (8, 8))
        # endregion
        name = pygame.font.match_font('nanumgothic,notosanscjkkr,malgungothic,applesdgothicneo')
        font = pygame.font.Font(name, 16)
        label = '방향키/WASD 이동 · Z/Space 발사 · Shift 집중 · X 폭탄' if name else 'WASD  Z/Space  Shift'
        self.help = font.render(label, True, (180, 220, 235))
        self.font, self.korean = font, name is not None
        self.hud_score, self.hud_lives, self.hud = -1, -1, None
        self.boss_phase, self.phase_label = -1, None
        self.hud_power, self.hud_bombs = -1, -1
    # endregion

    # region draw-player
    def draw_player(self, game, alpha):
        x = game.previous_x + (game.player_x - game.previous_x) * alpha
        y = game.previous_y + (game.player_y - game.previous_y) * alpha
        if game.previous_input & 32:
            pygame.draw.ellipse(self.screen, (80, 150, 180), (round(x) - 16, round(y) - 16, 33, 33), 1)
        if game.invulnerable // 6 % 2 == 0:
            self.screen.blit(self.player, (round(x) - 12, round(y) - 12))
        pygame.draw.circle(self.screen, (110, 240, 255), (round(x), round(y)), 2)
    # endregion

    # region draw-bullets
    def draw_bullets(self, game, alpha):
        pool = game.bullets
        for i in range(pool.count):
            x = pool.x[i] + pool.vx[i] * (alpha - 1)
            y = pool.y[i] + pool.vy[i] * (alpha - 1)
            if pool.kind[i] == 1:
                self.screen.blit(self.enemy_bullet, (round(x) - 4, round(y) - 4))
            else:
                pygame.draw.circle(self.screen, (100, 220, 255), (round(x), round(y)), max(1, round(pool.radius[i])))
    # endregion


    # region draw-enemies
    def draw_enemies(self, game, alpha):
        pool = game.enemies
        for i in range(pool.count):
            x = pool.x[i] + pool.vx[i] * (alpha - 1)
            y = pool.y[i] + pool.vy[i] * (alpha - 1)
            image = self.boss if pool.kind[i] == 1 else self.enemy
            half = image.get_width() // 2
            self.screen.blit(image, (round(x) - half, round(y) - half))
    # endregion

    # region draw-hud
    def draw_hud(self, game):
        if (self.hud_score != game.score or self.hud_lives != game.lives
                or self.hud_power != game.power or self.hud_bombs != game.bombs):
            label = f'S {game.score}  L {game.lives}  P {game.power}  B {game.bombs}'
            self.hud = self.font.render(label, True, (230, 235, 255))
            self.hud_score, self.hud_lives = game.score, game.lives
            self.hud_power, self.hud_bombs = game.power, game.bombs
        self.screen.blit(self.hud, (10, 32))
    # endregion


    # region boss-bar
    def draw_boss_bar(self, game):
        index = game.find_boss()
        if index < 0:
            return
        ratio = max(0.0, min(1.0, game.enemies.hp[index] / 180))
        pygame.draw.rect(self.screen, (30, 40, 60), (12, 58, 456, 10))
        pygame.draw.rect(self.screen, (255, 100, 120), (12, 58, round(456 * ratio), 10))
        if self.boss_phase != game.phase:
            label = f'보스 {game.phase}단계' if self.korean else str(game.phase)
            self.phase_label = self.font.render(label, True, (255, 185, 195))
            self.boss_phase = game.phase
        self.screen.blit(self.phase_label, (12, 74))
    # endregion

    # region draw-items
    def draw_items(self, game, alpha):
        pool = game.items
        for i in range(pool.count):
            x = round(pool.x[i] + pool.vx[i] * (alpha - 1))
            y = round(pool.y[i] + pool.vy[i] * (alpha - 1))
            pygame.draw.circle(self.screen, (255, 210, 80), (x, y), 6)
    # endregion

    # region draw-particles
    def draw_particles(self, game, alpha):
        pool = game.particles
        for i in range(pool.count):
            x = round(pool.x[i] + pool.vx[i] * (alpha - 1))
            y = round(pool.y[i] + pool.vy[i] * (alpha - 1))
            pygame.draw.circle(self.screen, (255, 190, 90), (x, y), 2)
    # endregion

    # region draw-overlay
    def draw_overlay(self, game):
        if game.status == 1 and not game.paused:
            return
        pygame.draw.rect(self.screen, (20, 40, 60), (60, 260, 360, 120))
        labels = ('탄막 슈팅', '', '게임 오버', '스테이지 완료')
        english = ('DANMAKU', '', 'GAME OVER', 'STAGE CLEAR')
        label = '일시 정지 · P' if game.paused else labels[game.status]
        if not self.korean:
            label = 'PAUSED - P' if game.paused else english[game.status]
        self.screen.blit(self.font.render(label, True, (255, 230, 160)), (90, 285))
        hint = f'Enter · BEST {game.high_score}'
        self.screen.blit(self.font.render(hint, True, (220, 235, 255)), (90, 325))
    # endregion

    # region draw-frame
    def draw(self, game, alpha):
        if game.paused or game.status != 1:
            alpha = 1.0
        self.screen.fill((8, 21, 35))
        self.draw_enemies(game, alpha)
        self.draw_bullets(game, alpha)
        self.draw_items(game, alpha)
        self.draw_particles(game, alpha)
        self.draw_player(game, alpha)
        self.screen.blit(self.help, (10, 10))
        self.draw_hud(game)
        self.draw_boss_bar(game)
        self.draw_overlay(game)
    # endregion
